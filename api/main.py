# ============================================================
# main.py
# ------------------------------------------------------------
# Purpose: FastAPI app that exposes our pipeline as HTTP endpoints.
#
#   POST   /ingest       — upload a PDF, run the full ingestion pipeline
#   POST   /search        — semantic search, returns chunks + bounding boxes
#   GET    /pdf/{id}      — serve the actual PDF file for the viewer
#   GET    /pdfs          — list the current user's PDFs
#   DELETE /pdfs/{id}     — delete a PDF (and its chunks) owned by the user
#   GET    /health         — health check
#
# Every route below is scoped to the logged-in user via
# get_current_user_id(), which verifies the Supabase JWT sent
# in the Authorization header. There is no more shared
# TEST_USER_ID — each of your pilot users only ever sees and
# touches their own documents.
# ============================================================

import os
import sys
import shutil
import uuid

from dotenv import load_dotenv

# Load .env before anything else so all env vars are available
# (including SUPABASE_JWT_SECRET used in auth.py)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth import get_current_user_id
from api.storage import upload_pdf as storage_upload, download_pdf as storage_download, delete_pdf as storage_delete
from ingestion.ingest import ingest_pdf
from ingestion.embedder import Embedder
from search.search import search_pdf
from highlighting.highlighter import find_passage_boxes
from Database.db import get_connection

print("[startup] Loading embedding model (shared across all requests)...")
EMBEDDER = Embedder()
print("[startup] Embedding model ready.")

# Where uploaded PDFs are stored. On Railway, mount a persistent volume
# and set UPLOAD_DIR to point inside it (e.g. /data/uploads) so files
# survive redeploys. Falls back to a local folder for local dev.
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Comma-separated list of allowed frontend origins, e.g.
# "https://your-app.vercel.app,http://localhost:5173"
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = ["*"] if _origins_env.strip() == "*" else [
    o.strip() for o in _origins_env.split(",") if o.strip()
]

app = FastAPI(title="Study PDF Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# POST /ingest
# ============================================================
@app.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    clean_filename = os.path.basename(
        file.filename.replace("/", os.sep).replace("\\", os.sep)
    )

    unique_name = f"{uuid.uuid4()}_{clean_filename}"
    # Save temporarily to disk so the ingestion pipeline can read it
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    print(f"[/ingest] Saved temp file: {save_path}")

    try:
        pdf_id = ingest_pdf(
            pdf_path=save_path,
            user_id=user_id,
            filename=clean_filename,
            embedder=EMBEDDER,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Clean up the temp file on failure
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    # ── Upload to Supabase Storage ──────────────────────────────────────────
    try:
        with open(save_path, "rb") as f:
            pdf_bytes = f.read()
        storage_path = storage_upload(user_id, unique_name, pdf_bytes)
    except Exception as e:
        print(f"[/ingest] WARNING: Supabase Storage upload failed: {e}", flush=True)
        # Fall back: keep the local path so the PDF is still usable locally
        storage_path = save_path
    else:
        # Successfully stored in Supabase — update DB with storage path
        # and remove the local temp file
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE pdfs SET file_path = %s WHERE id = %s AND user_id = %s",
            (storage_path, str(pdf_id), user_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        os.remove(save_path)
        print(f"[/ingest] Temp file removed, PDF stored in Supabase at: {storage_path}")

    return {
        "success": True,
        "pdf_id": str(pdf_id),
        "filename": clean_filename,
        "message": "PDF ingested successfully.",
    }


# ============================================================
# POST /search
# ============================================================
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
async def search(
    request: SearchRequest,
    user_id: str = Depends(get_current_user_id),
):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = search_pdf(
        query=request.query,
        top_k=request.top_k,
        user_id=user_id,
        embedder=EMBEDDER,
    )

    if not results:
        return {"query": request.query, "results": []}

    conn = get_connection()
    cur = conn.cursor()

    enriched = []
    for r in results:
        # Ownership check is implicit here: search_pdf() only ever
        # searches the calling user's own turbovec index, so results
        # can only belong to this user's PDFs. We still scope this
        # lookup by user_id as defense in depth.
        cur.execute(
            "SELECT filename, file_path FROM pdfs WHERE id = %s AND user_id = %s",
            (str(r["pdf_id"]), user_id),
        )
        pdf_row = cur.fetchone()

        if not pdf_row:
            continue

        original_filename = pdf_row[0]
        file_path = pdf_row[1]

        boxes = find_passage_boxes(
            pdf_path=file_path,
            page_number=r["page_number"],
            search_text=r["chunk_text"],
        )

        enriched.append({
            "pdf_id":            str(r["pdf_id"]),
            "original_filename": original_filename,
            "page_number":       r["page_number"],
            "chunk_text":        r["chunk_text"],
            "score":             r["score"],
            "bounding_boxes":    boxes,
        })

    cur.close()
    conn.close()

    return {"query": request.query, "results": enriched}


# ============================================================
# GET /pdf/{pdf_id}
# ============================================================
@app.get("/pdf/{pdf_id}")
async def serve_pdf(
    pdf_id: str,
    user_id: str = Depends(get_current_user_id),
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT file_path FROM pdfs WHERE id = %s AND user_id = %s",
        (pdf_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="PDF not found.")

    file_path = row[0]

    # Detect whether file_path is a Supabase Storage path (user_id/filename)
    # or a legacy local absolute path
    is_local = os.path.isabs(file_path) or file_path.startswith(".")

    if is_local:
        # Legacy local path (dev fallback)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file missing from disk.")
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
    else:
        # Supabase Storage path — download via service role key
        try:
            pdf_bytes = storage_download(file_path)
        except Exception as e:
            print(f"[/pdf] Storage download failed for {file_path}: {e}", flush=True)
            raise HTTPException(status_code=404, detail="PDF could not be retrieved from storage.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )


# ============================================================
# GET /pdfs
# ============================================================
@app.get("/pdfs")
async def list_pdfs(user_id: str = Depends(get_current_user_id)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, total_pages, upload_date FROM pdfs WHERE user_id = %s ORDER BY upload_date DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "pdfs": [
            {"id": str(r[0]), "filename": r[1], "total_pages": r[2], "upload_date": str(r[3])}
            for r in rows
        ]
    }


# ============================================================
# DELETE /pdfs/{pdf_id}
# ============================================================
@app.delete("/pdfs/{pdf_id}")
async def delete_pdf(
    pdf_id: str,
    user_id: str = Depends(get_current_user_id),
):
    conn = get_connection()
    cur = conn.cursor()

    # Confirm this PDF actually belongs to the caller before touching anything
    cur.execute(
        "SELECT file_path FROM pdfs WHERE id = %s AND user_id = %s",
        (pdf_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="PDF not found.")

    # Grab the chunk ids BEFORE deleting them, so we can also drop their
    # vectors from the user's turbovec index — otherwise deleted PDFs
    # would keep showing up in future search results.
    cur.execute("SELECT id FROM chunks WHERE pdf_id = %s AND user_id = %s", (pdf_id, user_id))
    chunk_ids = [r[0] for r in cur.fetchall()]

    cur.execute("DELETE FROM chunks WHERE pdf_id = %s AND user_id = %s", (pdf_id, user_id))
    cur.execute("DELETE FROM pdfs WHERE id = %s AND user_id = %s", (pdf_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

    # Delete from Supabase Storage or local disk
    file_path = row[0]
    if file_path:
        is_local = os.path.isabs(file_path) or file_path.startswith(".")
        if is_local:
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            try:
                storage_delete(file_path)
            except Exception as e:
                print(f"[delete_pdf] Storage delete failed for {file_path}: {e}", flush=True)

    if chunk_ids:
        try:
            from vectorstore.turbovec_store import load_or_create_index, remove_chunks, save_index

            index = load_or_create_index(user_id, dim=EMBEDDER.model.get_sentence_embedding_dimension())
            remove_chunks(index, chunk_ids)
            save_index(index, user_id)
        except Exception as e:
            # Don't fail the whole delete over an index cleanup issue —
            # log it so it's visible, but the PDF is already gone from
            # Postgres and disk either way.
            print(f"[delete_pdf] Warning: could not clean up turbovec index: {e}")

    return {"success": True}


# ============================================================
# GET /health
# ============================================================
@app.get("/health")
async def health():
    return {"status": "ok"}
