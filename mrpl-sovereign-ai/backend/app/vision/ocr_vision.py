"""Local OCR for scanned PDFs and images."""

import os
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps
from pdf2image import convert_from_path

TESSERACT_PATH = Path(r"C:\Users\ASUS\tesseract.exe")
TESSDATA_DIR = Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata")

if not TESSERACT_PATH.is_file():
    raise RuntimeError(f"Tesseract executable was not found: {TESSERACT_PATH}")
if not (TESSDATA_DIR / "eng.traineddata").is_file():
    raise RuntimeError(f"English OCR data was not found: {TESSDATA_DIR / 'eng.traineddata'}")

os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)
pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


def _prepare(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    return ImageOps.autocontrast(grayscale)


def tesseract_extract_from_image(image_path: str) -> str:
    image = _prepare(Image.open(image_path))
    return pytesseract.image_to_string(
        image,
        lang="eng",
        config="--oem 3 --psm 6",
    ).strip()


def tesseract_extract_from_scanned_pdf(
    pdf_path: str,
    dpi: int = 300,
) -> str:
    source = Path(pdf_path)
    if not source.is_file():
        raise FileNotFoundError(f"Scanned PDF was not found: {source}")

    pages = convert_from_path(str(source), dpi=dpi)
    extracted = []

    for number, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(
            _prepare(page),
            lang="eng",
            config="--oem 3 --psm 6",
        ).strip()
        if text:
            extracted.append(f"--- Page {number} ---\n{text}")

    result = "\n\n".join(extracted).strip()
    if not result:
        raise ValueError("OCR completed but no readable text was detected.")
    return result
