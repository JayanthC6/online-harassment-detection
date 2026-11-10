"""
ShieldAI OCR Module
Extracts text from images (screenshots) using OCRService (RapidOCR offline primary,
with Tesseract fallback), then performs threat classification.
"""
import os
import sys
from typing import Dict, Any, Callable, Union

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def extract_text(file_path: str) -> str:
    """
    Extracts text from an image using OCRService.
    """
    from services.ocr_service import OCRService
    return OCRService.extract_text(file_path)


def extract_text_and_meta(file_path: str) -> Dict[str, Any]:
    """
    Extracts text and extraction metadata (confidence, engine, warnings).
    """
    from services.ocr_service import OCRService
    return OCRService.extract_text_and_confidence(file_path)


def extract_and_classify(file_path: str, classifier: Union[str, Callable] = "baseline") -> Dict[str, Any]:
    """
    Full pipeline: image file -> OCR text -> threat classification.
    """
    ocr_meta = extract_text_and_meta(file_path)
    extracted = ocr_meta.get("text", "")
    ocr_conf = ocr_meta.get("confidence", 0.0)
    ocr_warning = ocr_meta.get("warning")

    if not extracted or not extracted.strip():
        return {
            "label": "no_text_found",
            "primary_label": "no_text_found",
            "category": "no_text_found",
            "level": "no_text_found",
            "safety_status": "unverified",
            "severity_tier": "info",
            "threat_score": None,
            "risk_score": None,
            "confidence": 0.0,
            "extracted_text": "",
            "explanation": "No readable text detected in image.",
            "warning": "No readable text detected in screenshot. Ensure the image is upright, legible, and not blank.",
            "ocr_warning": "No text detected by OCR engine (confidence 0.0).",
            "note": "No readable text detected in image.",
            "which_layer": "ocr",
            "model": ocr_meta.get("engine", "rapidocr-onnxruntime")
        }

    if callable(classifier):
        result = classifier(extracted)
    elif classifier == "distilbert":
        from predict_transformer import predict_message
        result = predict_message(extracted)
    else:
        try:
            from services.prediction_service import PredictionService
            result = PredictionService.classify_text(extracted)
        except Exception:
            from predict import predict_message
            result = predict_message(extracted)

    result["extracted_text"] = extracted
    result["ocr_confidence"] = ocr_conf
    if ocr_warning:
        result["ocr_warning"] = ocr_warning

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr.py path/to/image.png")
        sys.exit(1)

    res = extract_and_classify(sys.argv[1])
    print(f"Extracted text: {res.get('extracted_text')}")
    print(f"Level: {res.get('level')} Category: {res.get('category')} Confidence: {res.get('confidence')}")
