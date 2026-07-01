

import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")




def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def insert_pdf(user_id, filename, file_path, total_pages):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pdfs (user_id, filename, file_path, total_pages, status)
        VALUES (%s, %s, %s, %s, 'ready')
        RETURNING id
        """,
        (user_id, filename, file_path, total_pages)
    )

    pdf_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return pdf_id


def insert_chunk(pdf_id, user_id, page_number, section_type, title, text_content, embedding, raw_text):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO chunks (pdf_id, user_id, page_number, section_type, title, text_content, embedding, raw_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (pdf_id, user_id, page_number, section_type, title, text_content, embedding, raw_text)
    )

    conn.commit()
    cur.close()
    conn.close()


def insert_chunks_batch(chunks_with_embeddings, conn):
    cur = conn.cursor()
    inserted_ids = []

    for c in chunks_with_embeddings:
        # Strip NUL characters from all string fields — some PDFs contain
        # null bytes (0x00) which Postgres rejects in string columns
        def clean(s):
            return s.replace("\x00", "") if isinstance(s, str) else s

        cur.execute(
            """
            INSERT INTO chunks (pdf_id, user_id, page_number, section_type, title, text_content, embedding, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                c["pdf_id"], c["user_id"], c["page_number"],
                clean(c["section_type"]),
                clean(c["title"]) if c["title"] else None,
                clean(c["text_content"]),
                c["embedding"],
                clean(c["raw_text"]) if c.get("raw_text") else None
            )
        )
        inserted_ids.append(cur.fetchone()[0])

    conn.commit()
    cur.close()
    return inserted_ids
