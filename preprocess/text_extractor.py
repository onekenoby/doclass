# preprocess/text_extractor.py
import fitz  # PyMuPDF
import docx
import mimetypes
from pdf2image import convert_from_path
from preprocess.ocr_extractor import ocr_from_image

def extract_text_from_file(filepath):
    mime = mimetypes.guess_type(filepath)[0]

    if mime == 'application/pdf':
        doc = fitz.open(filepath)
        text = " ".join([page.get_text() for page in doc])
        if not text.strip():
            images = convert_from_path(filepath)
            text = " ".join([ocr_from_image(image) for image in images])
        return text

    elif mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        doc = docx.Document(filepath)
        return " ".join([para.text for para in doc.paragraphs])

    elif mime and mime.startswith("image"):
        return ocr_from_image(filepath)

    else:
        raise ValueError("Unsupported file type")
