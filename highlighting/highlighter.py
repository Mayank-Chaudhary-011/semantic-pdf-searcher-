# ============================================================
# highlighter.py
# ------------------------------------------------------------
# Purpose: Given a search result (pdf path, page number, and
# the chunk text we found), locate that exact passage inside
# the actual PDF file and return its bounding box coordinates.
#
# Unchanged from what you shared.
# ============================================================

import fitz  # PyMuPDF


def get_search_snippet(search_text: str, max_length: int = 100, min_length: int = 50):
    snippet = search_text[:max_length].strip()
    if len(search_text) > max_length:
        last_space = snippet.rfind(" ")
        if last_space > min_length:
            snippet = snippet[:last_space]
    return snippet.strip()


def find_passage_boxes(pdf_path: str, page_number: int, search_text: str):
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]

    search_snippet = get_search_snippet(search_text)
    rects = page.search_for(search_snippet)

    if not rects:
        words = search_text.strip().split()
        fallback_snippet = " ".join(words[:6])
        rects = page.search_for(fallback_snippet)

    doc.close()

    if not rects:
        return []

    boxes = []
    for rect in rects:
        boxes.append({
            "x0": round(rect.x0, 2),
            "y0": round(rect.y0, 2),
            "x1": round(rect.x1, 2),
            "y1": round(rect.y1, 2),
        })

    return boxes


def highlight_pdf_and_save(pdf_path: str, page_number: int, search_text: str, output_path: str):
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]

    search_snippet = get_search_snippet(search_text)
    rects = page.search_for(search_snippet)

    if not rects:
        words = search_text.strip().split()
        fallback_snippet = " ".join(words[:6])
        rects = page.search_for(fallback_snippet)

    if not rects:
        print(f"[highlighter] Warning: passage not found on page {page_number}")
    else:
        for rect in rects:
            highlight = page.add_highlight_annot(rect)
            highlight.update()
        print(f"[highlighter] Found and highlighted {len(rects)} match(es) on page {page_number}")

    doc.save(output_path)
    doc.close()
    print(f"[highlighter] Saved highlighted PDF to: {output_path}")
