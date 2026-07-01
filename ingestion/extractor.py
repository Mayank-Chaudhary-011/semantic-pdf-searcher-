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


def extract_text_with_ocr_fallback(pdf_path):
    """
    Main entry point: return a list of {"page": N, "text": "...", "used_ocr": bool}
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
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
