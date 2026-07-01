import os
from pathlib import Path
from turbovec import IdMapIndex
import numpy as np

# On Railway, attach a persistent volume and set TURBOVEC_INDEX_DIR to a
# path inside it (e.g. /data/turbovec_indexes) so search indexes survive
# redeploys. Falls back to a local folder next to this file for dev.
INDEX_DIR = Path(
    os.getenv(
        "TURBOVEC_INDEX_DIR",
        os.path.join(os.path.dirname(__file__), "..", "turbovec_indexes"),
    )
)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

BIT_WIDTH = 4


def _index_path(user_id):
    return INDEX_DIR / f"{user_id}.tvim"


def load_or_create_index(user_id, dim):
    path = _index_path(user_id)
    if path.exists():
        return IdMapIndex.load(str(path))
    return IdMapIndex(dim=dim, bit_width=BIT_WIDTH)


def save_index(index, user_id):
    index.write(str(_index_path(user_id)))


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
