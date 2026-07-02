import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.embedder import Embedder
from Database.db import get_connection

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vectorstore"))
from turbovec_store import load_or_create_index, search_chunks

RELEVANCE_THRESHOLD = 0.30   # was 0.45 — lowered so similar-context PDFs surface



def search_pdf(query, top_k=5, user_id=None, exclude_references=True, pdf_id=None, embedder=None):
    """
    Args:
        embedder: an already-loaded Embedder instance to reuse (recommended —
            loading the model fresh on every search is what was making
            searches slow). If not given, a new one is loaded for this
            call only (fine for standalone script use, not for a live API).
    """
    print(f"[search] Embedding query: '{query}'")
    if embedder is None:
        embedder = Embedder()

    query_vector = embedder.embed_text(query)
    dim = embedder.model.get_sentence_embedding_dimension()

    index = load_or_create_index(user_id, dim=dim)

    conn = get_connection()
    cursor = conn.cursor()

    allowed_ids = None
    if pdf_id is not None:
        cursor.execute("SELECT id FROM chunks WHERE pdf_id = %s AND user_id = %s;", (pdf_id, user_id))
        allowed_ids = [row[0] for row in cursor.fetchall()]
        if not allowed_ids:
            cursor.close()
            conn.close()
            return []

    # Fetch more candidates than requested from the index — after the
    # RELEVANCE_THRESHOLD filter we may lose some, so over-fetching ensures
    # we always return top_k meaningful results across all user PDFs.
    fetch_k = max(top_k * 3, top_k + 10)
    scores, chunk_ids = search_chunks(index, query_vector, k=fetch_k, allowed_ids=allowed_ids)

    if len(chunk_ids) == 0:
        cursor.close()
        conn.close()
        return []

    ids_list = [int(i) for i in chunk_ids]
    section_filter_sql = "AND c.section_type != 'reference'" if exclude_references else ""

    query_sql = f"""
        SELECT
            c.id, c.pdf_id, c.page_number, c.text_content, c.raw_text, c.section_type
        FROM chunks c
        WHERE c.id = ANY(%s) AND c.user_id = %s {section_filter_sql};
    """
    cursor.execute(query_sql, (ids_list, user_id))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    score_by_id = {int(i): float(s) for i, s in zip(chunk_ids, scores)}

    results = []
    for row in rows:
        chunk_id = row[0]
        score = round(score_by_id.get(chunk_id, 0), 4)

        if score < RELEVANCE_THRESHOLD:
            continue

        results.append({
            "chunk_id": chunk_id,
            "pdf_id": row[1],
            "page_number": row[2],
            "chunk_text": row[3],
            "raw_text": row[4],
            "score": score,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    test_query = "Large language model"

    print(f"\n=== Search Test ===")
    print(f"Query: {test_query}\n")

    results = search_pdf(query=test_query, top_k=5)

    if not results:
        print("No results found. Make sure you've run ingestion first.")
    else:
        for i, r in enumerate(results, 1):
            print(f"--- Result {i} ---")
            print(f"  PDF ID    : {r['pdf_id']}")
            print(f"  Page      : {r['page_number']}")
            print(f"  Score     : {r['score']}")
            print(f"  Text      : {r['chunk_text'][:200]}...")
            print()
