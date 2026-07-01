# ============================================================
# make_fake_scan.py
# ------------------------------------------------------------
# Purpose: Take a real, text-based PDF and convert ONE of its
# pages into a pure image (no embedded text at all) — basically
# simulating what a scanned/photographed page looks like to a
# computer. This gives us a realistic test case for the OCR
# fallback path in extractor.py, without needing to actually
# scan or photograph anything.
#
# How it works: we render the page as a picture (just pixels,
# no text layer), then save that picture as a brand new
# single-page PDF. To a computer, this new PDF has zero
# extractable text — exactly like a real scanned document.
# ============================================================

import fitz  # PyMuPDF


def make_fake_scanned_pdf(source_pdf_path, page_number, output_path):
    """
    Converts one page of a real PDF into an image-only PDF.

    Args:
        source_pdf_path (str): path to the real PDF to take a page from
        page_number (int): which page to convert (0-indexed, so 0 = first page)
        output_path (str): where to save the new "fake scanned" PDF
    """
    # Open the original PDF
    source_doc = fitz.open(source_pdf_path)

    # Grab the specific page we want to convert
    page = source_doc[page_number]

    # Render that page as a picture (pixmap), same as we do in OCR —
    # this is the "taking a screenshot of the page" step
    pix = page.get_pixmap(dpi=200)

    # Create a brand new, empty PDF document
    new_doc = fitz.open()

    # Add a blank page to it, matching the original page's dimensions
    new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

    # Insert the rendered image into that blank page.
    # Crucially: this puts PIXELS on the page, not real text —
    # so when extractor.py later tries page.get_text(), it will
    # get nothing back, correctly triggering the OCR fallback.
    new_page.insert_image(new_page.rect, pixmap=pix)

    # Save the new image-only PDF to disk
    new_doc.save(output_path)
    new_doc.close()
    source_doc.close()

    print(f"Created fake scanned PDF at: {output_path}")


if __name__ == "__main__":
    # Using your existing RAG survey PDF as the source —
    # change this path if needed
    source = r"C:\Users\Lenovo\Downloads\2312.10997v5.pdf"

    # Take page 1 (index 0) and turn it into an image-only PDF
    make_fake_scanned_pdf(
        source_pdf_path=source,
        page_number=0,
        output_path=r"D:\study-pdf-search\fake_scan_test.pdf"
    )