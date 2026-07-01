# ============================================================
# backfill_turbovec.py
# ------------------------------------------------------------
# Purpose: One-time repair script for PDFs that were ingested
# BEFORE the turbovec-index-to-Supabase fix. Those PDFs have
# their chunks safely in Postgres, but their turbovec index
# file was lost when the Railway container restarted (local
# disk is ephemeral).
#
# This script rebuilds each user's turbovec index directly from
# the embeddings already stored in the `chunks` table, then
# saves it — which now also uploads it to Supabase Storage
# thanks to the updated turbovec_store.py.
#
# Run this ONCE after deploying the turbovec_store.py fix.
# Safe to run multiple times (it just rebuilds from scratch
# each time, same result).
#
# Usage:
#   python backfill_turbovec.py                 # backfill ALL users
#   python backfill_turbovec.py <user_id>        # backfill one user only
# ============================================================

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Database"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorstore"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingestion"))

from db import get_connection
from turbovec_store import load_or_create_index, add_chunks, save_index
from embedder import Embedder


def backfill_user(user_id, embedder, conn):
    print(f"\n=== Backfilling user {user_id} ===")

    cur = conn.cursor()
    cur.execute(
        "SELECT id, embedding FROM chunks WHERE user_id = %s ORDER BY id;",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        print(f"  No chunks found for this user — skipping.")
        return

    chunk_ids = [r[0] for r in rows]

    def to_vector(e):
        if isinstance(e, str):
            return json.loads(e)
        return e

    embeddings = [to_vector(r[1]) for r in rows]

    dim = embedder.model.get_embedding_dimension()

    # Start from a completely fresh index (NOT load_or_create_index's
    # remote-download path) — we're rebuilding from scratch on purpose,
    # in case the old remote index is stale, partial, or corrupted.
    from turbovec import IdMapIndex
    index = IdMapIndex(dim=dim, bit_width=4)

    add_chunks(index, chunk_ids, embeddings)
    save_index(index, user_id)  # this also uploads to Supabase Storage

    print(f"  Rebuilt index with {len(chunk_ids)} chunks and uploaded to Supabase.")


def main():
    embedder = Embedder()
    conn = get_connection()

    if len(sys.argv) > 1:
        # Backfill just one user
        user_id = sys.argv[1]
        backfill_user(user_id, embedder, conn)
    else:
        # Backfill every user who has at least one chunk
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT user_id FROM chunks;")
        user_ids = [r[0] for r in cur.fetchall()]
        cur.close()

        print(f"Found {len(user_ids)} user(s) with chunks to backfill.")
        for user_id in user_ids:
            backfill_user(user_id, embedder, conn)

    conn.close()
    print("\n=== Backfill complete ===")


if __name__ == "__main__":
    main()