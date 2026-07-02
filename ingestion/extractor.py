import os
import fitz
from PIL import Image
import io
import pytesseract

# On Windows dev machines, Tesseract isn't on PATH by default, so we point
# to it explicitly via an env var. On the Linux container (Railway), the
# Dockerfile installs the `tesseract-ocr` apt package, which puts it on
# PATH automatically — no override needed there.
_tesseract_cmd = os.getenv("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


def needs_ocr(page_text, word_threshold=10):
    """
    If a page's extracted text is too short, it's likely a scanned image,
    not real embedded text.
    """
    word_count = len(page_text.strip().split())
    return word_count < word_threshold


def ocr_page(doc, page_num):
    """
    Renders a page as an image and runs OCR on it.
    """
    page = doc[page_num]
    pix = page.get_pixmap(dpi=300)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    return pytesseract.image_to_string(img)


def extract_page_text_in_reading_order(page):
    """
    Extract text from a single PDF page using block-level reading order.

    PyMuPDF's raw get_text() on multi-column layouts interleaves left and
    right column lines, producing fragments like "left", "right", etc. as
    separate lines. Using "blocks" mode gives us text organized by bounding
    box, which we sort top-to-bottom then left-to-right — matching the
    natural reading order and keeping each column's paragraph intact.

    Each block tuple: (x0, y0, x1, y1, text, block_no, block_type)
    We sort by (y0 // ROW_BAND, x0) so horizontally adjacent columns stay
    in reading order while vertically stacked blocks stay sequential.
    """
    ROW_BAND = 20   # px tolerance — blocks within 20px vertical are "same row"

    blocks = page.get_text("blocks")  # list of (x0, y0, x1, y1, text, block_no, block_type)
    # block_type 0 = text, 1 = image
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

    # Sort by (row band, x0) for correct reading order in multi-column layouts
    text_blocks.sort(key=lambda b: (int(b[1] / ROW_BAND), b[0]))

    paragraphs = []
    for block in text_blocks:
        raw = block[4]
        # Normalise within-block whitespace: join hyphenated line breaks,
        # collapse multiple spaces, strip leading/trailing whitespace.
        text = raw.replace("-\n", "")        # de-hyphenate line breaks
        text = " ".join(text.split())         # collapse all whitespace
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_text_with_ocr_fallback(pdf_path):
    """
    Main entry point: return a list of {"page": N, "text": "...", "used_ocr": bool}
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Use reading-order block extraction first
        text = extract_page_text_in_reading_order(page)
        used_ocr = False

        if needs_ocr(text):
            text = ocr_page(doc, page_num)
            used_ocr = True

        pages.append({
            "page": page_num + 1,
            "text": text,
            "used_ocr": used_ocr
        })

    doc.close()
    return pages


if __name__ == "__main__":
    test_pdf = r"C:\Users\Lenovo\Downloads\2312.10997v5.pdf"

    pages = extract_text_with_ocr_fallback(test_pdf)

    for p in pages:
        tag = "[OCR]" if p["used_ocr"] else "[TEXT]"
        print(f"{tag} Page{p['page']} : {len(p['text'])}chars")
        print(p["text"][:200])
        print("---")
