# ============================================================
# chat.py
# ------------------------------------------------------------
# Purpose: Let users ask follow-up questions about a PDF.
#
# Instead of sending the ENTIRE PDF as context (expensive, and
# most LLMs perform worse with huge irrelevant context), we:
#   1. Embed the user's question
#   2. Find the most relevant chunks from THIS PDF only
#   3. Send only those chunks + the question to GPT-4o-mini
#
# This keeps cost low and answer quality high — same principle
# as RAG (Retrieval Augmented Generation) itself.
# ============================================================

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.embedder import Embedder
from Database.db import get_connection

load_dotenv()
client = OpenAI()


def get_relevant_chunks_for_pdf(pdf_id: str, question: str, embedder: Embedder, top_k: int = 10):
    """
    Finds the most relevant chunks WITHIN A SPECIFIC PDF for a given question.
    This is just like search_pdf() but scoped to one PDF only.
    """
    query_vector = embedder.embed_text(question)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT page_number, text_content,
               1 - (embedding <=> %s::vector) AS score
        FROM chunks
        WHERE pdf_id = %s
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
        """,
        (query_vector, pdf_id, query_vector, top_k)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    chunks = []
    for row in rows:
        chunks.append({
            "page": row[0],
            "text": row[1],
            "score": round(float(row[2]), 4)
        })

    return chunks


def ask_question(pdf_id: str, question: str, chat_history: list, embedder: Embedder):
    """
    Answers a user's question about a specific PDF, using relevant
    chunks as context, and the existing chat history for continuity.

    Args:
        pdf_id        : which PDF the user is asking about
        question      : the user's current question
        chat_history  : list of {role, content} dicts from prior messages
        embedder      : shared Embedder instance (passed in, not reloaded)

    Returns:
        str: the assistant's answer
    """

    # ── Step 1: Retrieve relevant chunks for this question ───────
    chunks = get_relevant_chunks_for_pdf(pdf_id, question, embedder, top_k=10)

    if not chunks:
        return "I couldn't find relevant content in this PDF to answer that question."

    # ── Step 2: Build context string from chunks ──────────────────
    context_text = "\n\n".join([
        f"[Page {c['page']}]: {c['text']}" for c in chunks
    ])

    system_prompt = f"""You are a helpful study assistant. Answer the user's question 
based ONLY on the following content from their PDF document. If the answer isn't 
in the provided content, say so honestly — don't make things up.

Always mention which page(s) your answer comes from when relevant.

PDF CONTENT:
{context_text}
"""

    # ── Step 3: Build the full message list (system + history + new question) ──
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)  # prior conversation turns
    messages.append({"role": "user", "content": question})

    # ── Step 4: Call GPT-4o-mini ───────────────────────────────────
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3  # slightly creative but mostly factual
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"[chat] Error calling OpenAI: {e}")
        return "Sorry, I ran into an error answering that question. Please try again."


# ── Manual test ────────────────────────────────────────────────
if __name__ == "__main__":
    embedder = Embedder()

    answer = ask_question(
        pdf_id="1",
        question="Terrorism In India?",
        chat_history=[],
        embedder=embedder
    )

    print("\n=== Answer ===")
    print(answer)