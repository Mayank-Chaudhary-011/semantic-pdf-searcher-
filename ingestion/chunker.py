# ============================================================
# chunker.py — unchanged from what you shared, aside from
# trimming the manual __main__ test block.
# ============================================================

def create_chunks(pdf_id, page_number, page_text, min_length=50, max_length=1000):
    if not page_text or len(page_text.strip()) == 0:
        return []

    paragraphs = []
    current = []

    for line in page_text.splitlines():
        if line.strip() == "":
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
        else:
            current.append(line.strip())

    if current:
        paragraphs.append(" ".join(current).strip())

    chunks = []

    for para in paragraphs:
        if len(para) < min_length:
            continue

        if len(para) > max_length:
            sub_chunks = split_by_sentences(para, max_length)
        else:
            sub_chunks = [para]

        for chunk_text in sub_chunks:
            if len(chunk_text.strip()) < min_length:
                continue

            chunks.append({
                "pdf_id":       pdf_id,
                "page":         page_number,
                "section_type": "paragraph",
                "title":        None,
                "text":         chunk_text.strip(),
                "raw_text":     page_text
            })

    return chunks


def split_by_sentences(text, max_length):
    import re
    sentences = re.split(r'(?<=[.?!])\s+', text)

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
