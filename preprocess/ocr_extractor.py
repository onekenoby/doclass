import pytesseract
from PIL import Image

def ocr_from_image(image_path_or_obj):
    """
    Takes a file path or a PIL Image object and returns extracted text using OCR.
    """
    if isinstance(image_path_or_obj, str):
        image = Image.open(image_path_or_obj)
    else:
        image = image_path_or_obj

    return pytesseract.image_to_string(image)
