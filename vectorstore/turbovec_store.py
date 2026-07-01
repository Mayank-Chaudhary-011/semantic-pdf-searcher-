import os
import sys
from pathlib import Path
from turbovec import IdMapIndex
import numpy as np

# Needed to import storage.py from the api/ folder for Supabase upload/download.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "api"))
from storage import upload_index, download_index

# Local disk is now just scratch space — turbovec's IdMapIndex needs a real
# file path to load()/write() from, but it is NOT the source of truth
# anymore. The source of truth is Supabase Storage, because Railway's local
# disk is wiped on every redeploy/restart. On Railway you do NOT need to
# set TURBOVEC_INDEX_DIR or attach a volume anymore — this folder is
# rebuilt from Supabase automatically every time it's needed.
INDEX_DIR = Path(
    os.getenv(
        "TURBOVEC_INDEX_DIR",
        os.path.join(os.path.dirname(__file__), "..", "turbovec_indexes"),
    )
)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

BIT_WIDTH = 4


def _local_path(user_id):
    return INDEX_DIR / f"{user_id}.tvim"


def load_or_create_index(user_id, dim):
    local_path = _local_path(user_id)

    # Always try to pull the latest version from Supabase Storage first.
    # Local disk may be empty (fresh container, redeploy, restart) even
    # if this user has an index that was saved in a previous request.
    try:
        index_bytes = download_index(user_id)
        with open(local_path, "wb") as f:
            f.write(index_bytes)
        print(f"[turbovec] downloaded index for user {user_id} from Supabase Storage ({len(index_bytes)} bytes)", flush=True)
    except Exception as e:
        # This is expected and NORMAL for a brand new user who has never
        # ingested anything yet — not an error to worry about.
        print(f"[turbovec] no remote index found for user {user_id} ({type(e).__name__}) — starting fresh", flush=True)

    if local_path.exists():
        return IdMapIndex.load(str(local_path))
    return IdMapIndex(dim=dim, bit_width=BIT_WIDTH)


def save_index(index, user_id):
    local_path = _local_path(user_id)
    index.write(str(local_path))

    # Push to Supabase Storage immediately so it survives container
    # restarts/redeploys. If this upload fails, log loudly — a failed
    # upload here silently means "next search after a restart returns
    # nothing," which is exactly the bug we're fixing.
    with open(local_path, "rb") as f:
        index_bytes = f.read()
    try:
        upload_index(user_id, index_bytes)
        print(f"[turbovec] uploaded index for user {user_id} to Supabase Storage ({len(index_bytes)} bytes)", flush=True)
    except Exception as e:
        print(f"[turbovec] ERROR: failed to upload index to Supabase Storage: {e}", flush=True)


def add_chunks(index, chunk_ids, embeddings):
    ids_arr = np.array(chunk_ids, dtype=np.uint64)
    vecs_arr = np.array(embeddings, dtype=np.float32)
    index.add_with_ids(vecs_arr, ids_arr)


def search_chunks(index, query_vector, k=5, allowed_ids=None):
    query_arr = np.array([query_vector], dtype=np.float32)
    kwargs = {}
    if allowed_ids is not None:
        kwargs["allowlist"] = np.array(allowed_ids, dtype=np.uint64)
    scores, ids = index.search(query_arr, k=k, **kwargs)
    return scores[0], ids[0]


def remove_chunks(index, chunk_ids):
    for cid in chunk_ids:
        index.remove(int(cid))