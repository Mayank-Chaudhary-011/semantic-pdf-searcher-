# ============================================================
# storage.py
# ------------------------------------------------------------
# Purpose: Thin wrapper around Supabase Storage for uploading
# and downloading user PDFs.
#
# Bucket: "pdfs"  (private — only accessible via service_role key)
# Path pattern: {user_id}/{unique_name}
# ============================================================

import os
from functools import lru_cache
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = "PDF"


@lru_cache(maxsize=1)
def _client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env "
            "for Supabase Storage to work."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def upload_pdf(user_id: str, unique_name: str, file_bytes: bytes) -> str:
    """
    Upload a PDF to Supabase Storage.

    Returns the storage path (e.g. "abc-123/uuid_filename.pdf") which is
    stored in the database as file_path.
    """
    storage_path = f"{user_id}/{unique_name}"
    _client().storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    print(f"[storage] uploaded to bucket '{BUCKET}': {storage_path}", flush=True)
    return storage_path


def download_pdf(storage_path: str) -> bytes:
    """
    Download a PDF from Supabase Storage and return its raw bytes.
    """
    response = _client().storage.from_(BUCKET).download(storage_path)
    return response


def delete_pdf(storage_path: str) -> None:
    """
    Delete a PDF from Supabase Storage.
    """
    _client().storage.from_(BUCKET).remove([storage_path])
    print(f"[storage] deleted from bucket '{BUCKET}': {storage_path}", flush=True)
