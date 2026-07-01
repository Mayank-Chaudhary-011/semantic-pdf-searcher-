import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from extractor import extract_text_with_ocr_fallback
from chunker import create_chunks
from embedder import Embedder

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Database"))
from db import insert_pdf, insert_chunks_batch, get_connection

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vectorstore")))
from turbovec_store import load_or_create_index, add_chunks, save_index


def ingest_pdf(pdf_path, user_id, filename=None, embedder=None):
    """
    Args:
        embedder: an already-loaded Embedder instance to reuse (recommended —
            loading the model fresh on every call is slow). If not given,
            a new one is loaded just for this call (fine for standalone
            script use, not for a live API).
    """
    if filename is None:
        filename = os.path.basename(pdf_path)

    owns_embedder = embedder is None
    if owns_embedder:
        embedder = Embedder()

    print(f"\n=== Starting ingestion for: {filename} ===\n")

    print("[1/5] Extracting text from PDF...")
    pages = extract_text_with_ocr_fallback(pdf_path)
    print(f"      Extracted {len(pages)} pages.")

    print("[2/5] Creating PDF record in database...")
    pdf_id = insert_pdf(
        user_id=user_id,
        filename=filename,
        file_path=pdf_path,
        total_pages=len(pages)
    )
    print(f"      Created PDF record with id: {pdf_id}")

    print("[3/5] Using embedding model...")

    conn = get_connection()
    index = load_or_create_index(user_id, dim=embedder.model.get_sentence_embedding_dimension())

    total_chunks_created = 0

    print("[4/5] Processing each page (chunk + embed + store)...")

    for page_data in pages:
        page_number = page_data["page"]
        page_text = page_data["text"]

        if len(page_text.strip()) < 20:
            print(f"      Page {page_number}: skipped (too little text)")
            continue

        chunks = create_chunks(
            pdf_id=pdf_id,
            page_number=page_number,
            page_text=page_text
        )

        if not chunks:
            print(f"      Page {page_number}: no chunks produced")
            continue

        texts_to_embed = [c["text"] for c in chunks]
        embeddings = embedder.embed_batch(texts_to_embed)

        chunks_to_insert = []
        for chunk, embedding in zip(chunks, embeddings):
            chunks_to_insert.append({
                "pdf_id": pdf_id,
                "user_id": user_id,
                "page_number": chunk["page"],
                "section_type": chunk["section_type"],
                "title": chunk["title"],
                "text_content": chunk["text"],
                "embedding": embedding,
                "raw_text": chunk["raw_text"]
            })

        inserted_ids = insert_chunks_batch(chunks_to_insert, conn)
        add_chunks(index, inserted_ids, embeddings)
        total_chunks_created += len(chunks_to_insert)

        print(f"      Page {page_number}: {len(chunks)} chunks created and stored")

    conn.close()
    save_index(index, user_id)

    print(f"\n[5/5] Ingestion complete!")
    print(f"      PDF id: {pdf_id}")
    print(f"      Total chunks stored: {total_chunks_created}")

    return pdf_id


if __name__ == "__main__":
    TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

    pdf_path = r"C:\Users\Lenovo\Downloads\2312.10997v5.pdf"

    ingest_pdf(
        pdf_path=pdf_path,
        user_id=TEST_USER_ID,
        filename="RAG_Survey_Paper.pdf"
    )
