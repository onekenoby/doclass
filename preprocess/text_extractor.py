import fitz  # PyMuPDF
import docx
import mimetypes
from pdf2image import convert_from_path
from preprocess.ocr_extractor import ocr_from_image

def extract_text_from_file(filepath):
    """
    Extracts paragraphs of text from PDF or DOCX, falling back
    to OCR for scanned PDFs.
    Returns a list of paragraph strings.
    """
    mime = mimetypes.guess_type(filepath)[0]

    if mime == 'application/pdf':
        doc = fitz.open(filepath)
        text = " ".join([page.get_text() for page in doc])
        if not text.strip():
            images = convert_from_path(filepath)
            text = " ".join([ocr_from_image(image) for image in images])
    else:
        return extract_paragraphs_from_docx(filepath)

    paragraphs = []
    for page in doc:
        text_blocks = page.get_text("blocks")
        for block in text_blocks:
            block_text = block[4].strip()
            if block_text:
                paragraphs.append(block_text)

    return paragraphs


def extract_paragraphs_from_docx(filepath):
    doc = docx.Document(filepath)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]