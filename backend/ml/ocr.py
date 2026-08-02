"""
Extracts text from an image (screenshot) using EasyOCR, then hands the
extracted text to the existing text classifier (predict.py or predict_transformer.py).

First run downloads the EasyOCR models (~20MB for detection, ~10MB for English recognition).
These will be cached locally.

Usage:
    python ocr.py path/to/image.png
"""
import os
import sys

import easyocr

sys.path.append(os.path.dirname(__file__))

_reader = None

def _load_reader():
    global _reader
    if _reader is None:
        print("Loading EasyOCR model (first call only, may download weights)...")
        # Initialize the reader for English
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader

def extract_text(file_path: str) -> str:
    """
    Extracts text from an image using EasyOCR.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    reader = _load_reader()
    results = reader.readtext(file_path)
    
    # results is a list of tuples: (bbox, text, prob)
    # Join the extracted text blocks with spaces
    extracted = " ".join([res[1] for res in results])
    return extracted.strip()

def extract_and_classify(file_path: str, classifier="baseline") -> dict:
    """
    Full pipeline: image file -> OCR text -> harassment classification.
    """
    extracted = extract_text(file_path)

    if not extracted:
        return {
            "label": "non_harassing",
            "category": "none",
            "confidence": 1.0,
            "extracted_text": "",
            "note": "No readable text detected in image.",
        }

    if classifier == "distilbert":
        from predict_transformer import predict_message
    else:
        from predict import predict_message

    result = predict_message(extracted)
    result["extracted_text"] = extracted
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr.py path/to/image.png")
        sys.exit(1)

    result = extract_and_classify(sys.argv[1])
    print(f"Extracted text: {result['extracted_text']}")
    print(f"Label: {result['label']}  Category: {result['category']}  Confidence: {result['confidence']}")
