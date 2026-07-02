"""
chunker.py — Sentence-window chunking with overlap.

Instead of paragraph-splitting (which produces tiny chunks when paragraphs
are short or PDF extraction produces single-line "paragraphs"), we:

  1. Clean the raw text: filter out lines with fewer than MIN_LINE_WORDS
     words (these are artefacts like page numbers, column headers, etc.).
  2. Split the cleaned text into sentences using a regex.
  3. Build overlapping windows of WINDOW_SIZE sentences each, stepping by
     STEP_SIZE sentences. Adjacent windows share OVERLAP sentences so a
     passage that straddles two windows is still fully covered by at least
     one chunk.

This gives passages that are always coherent and contextually rich, which
makes semantic similarity search far more reliable.
"""

import re

# ─── tuning knobs ────────────────────────────────────────────────────────────
WINDOW_SIZE   = 6      # sentences per chunk
STEP_SIZE     = 3      # slide by 3 → 3-sentence overlap between neighbours
MIN_CHUNK_LEN = 80     # discard chunks shorter than this many characters
MIN_LINE_WORDS = 3     # lines with fewer words are treated as noise / headers
# ─────────────────────────────────────────────────────────────────────────────


def _clean_text(text: str) -> str:
    """
    Remove noise lines (very short lines, page numbers, isolated symbols)
    and normalise whitespace before sentence splitting.
    """
    lines = text.splitlines()
    good_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines — sentence splitter will handle paragraph breaks
        if not stripped:
            good_lines.append("")
            continue
        word_count = len(stripped.split())
        # Keep lines with at least MIN_LINE_WORDS real words
        if word_count >= MIN_LINE_WORDS:
            good_lines.append(stripped)
        # else: silently drop — these are headers, page numbers, column labels

    # Re-join, collapse multiple blank lines into one
    cleaned = "\n".join(good_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences. We use a simple but robust regex that handles:
      • Period / ! / ? as sentence endings
      • Common abbreviations (Mr., Dr., etc.) are partially protected by
        requiring a capital letter after the split point.
      • Newline-separated paragraphs always start a new sentence group.
    """
    # First, split on paragraph boundaries
    paragraphs = re.split(r"\n\n+", text)
    sentences = []
    sentence_end = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"])")

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Within each paragraph, split on sentence endings
        parts = sentence_end.split(para)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences


def create_chunks(pdf_id, page_number, page_text, min_length=MIN_CHUNK_LEN, max_length=2000):
    """
    Public API — same signature as before so ingest.py needs no changes.

    Returns a list of chunk dicts compatible with the existing schema.
    """
    if not page_text or len(page_text.strip()) == 0:
        return []

    cleaned = _clean_text(page_text)
    if len(cleaned.strip()) < min_length:
        return []

    sentences = _split_sentences(cleaned)
    if not sentences:
        return []

    chunks = []

    # Sliding-window over sentences
    for start in range(0, len(sentences), STEP_SIZE):
        window = sentences[start: start + WINDOW_SIZE]
        chunk_text = " ".join(window).strip()

        if len(chunk_text) < min_length:
            continue
        # Hard cap — truncate gracefully at a sentence boundary
        if len(chunk_text) > max_length:
            chunk_text = chunk_text[:max_length].rsplit(" ", 1)[0]

        chunks.append({
            "pdf_id":       pdf_id,
            "page":         page_number,
            "section_type": "paragraph",
            "title":        None,
            "text":         chunk_text,
            "raw_text":     page_text,
        })

    # De-duplicate: if the last chunk is almost identical to the second-last
    # (can happen when total sentences < WINDOW_SIZE), keep only unique ones.
    seen = set()
    unique_chunks = []
    for c in chunks:
        key = c["text"][:120]
        if key not in seen:
            seen.add(key)
            unique_chunks.append(c)

    return unique_chunks


# ─── Legacy helper kept for any external callers ──────────────────────────────
def split_by_sentences(text, max_length):
    """Kept for backwards compatibility — no longer used internally."""
    sentences = re.split(r"(?<=[.?!])\s+", text)
    sub_chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_length and current:
            sub_chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence
    if current.strip():
        sub_chunks.append(current.strip())
    return sub_chunks
