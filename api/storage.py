import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "pdfs"
INDEX_PREFIX = "_indexes"

_supabase: Client | None = None


def _client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase


def upload_pdf(user_id: str, filename: str, file_bytes: bytes) -> str:
    storage_path = f"{user_id}/{filename}"
    _client().storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    return storage_path


def download_pdf(storage_path: str) -> bytes:
    return _client().storage.from_(BUCKET).download(storage_path)


def delete_pdf(storage_path: str) -> None:
    _client().storage.from_(BUCKET).remove([storage_path])


def upload_index(user_id: str, file_bytes: bytes) -> str:
    storage_path = f"{INDEX_PREFIX}/{user_id}.tvim"
    _client().storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": "application/octet-stream", "upsert": "true"},
    )
    print(f"[storage] uploaded index to bucket '{BUCKET}': {storage_path}", flush=True)
    return storage_path


def download_index(user_id: str) -> bytes:
    storage_path = f"{INDEX_PREFIX}/{user_id}.tvim"
    return _client().storage.from_(BUCKET).download(storage_path)