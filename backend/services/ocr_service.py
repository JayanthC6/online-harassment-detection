"""
ShieldAI OCR Service
Provides pip-installable offline OCR via rapidocr-onnxruntime as primary engine,
with optional Tesseract OCR fallback.
"""
import os
import sys
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("ShieldAI.OCRService")

_rapid_ocr_instance = None


class OCRService:
    @classmethod
    def get_rapid_engine(cls):
        global _rapid_ocr_instance
        if _rapid_ocr_instance is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                _rapid_ocr_instance = RapidOCR()
                logger.info("Initialized RapidOCR offline engine.")
            except ImportError:
                logger.warning("rapidocr-onnxruntime not installed.")
                _rapid_ocr_instance = False
            except Exception as e:
                logger.warning(f"Failed to initialize RapidOCR: {e}")
                _rapid_ocr_instance = False
        return _rapid_ocr_instance if _rapid_ocr_instance is not False else None

    @classmethod
    def extract_text_and_confidence(cls, file_path: str) -> Dict[str, Any]:
        """
        Extracts text and confidence score from an image file.
        Returns:
            {
                "text": str,
                "confidence": float (0.0 - 1.0),
                "engine": str,
                "warning": Optional[str]
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # 1. Try RapidOCR as primary engine
        rapid_engine = cls.get_rapid_engine()
        if rapid_engine is not None:
            try:
                result, elapse = rapid_engine(file_path)
                if not result:
                    return {
                        "text": "",
                        "confidence": 0.0,
                        "engine": "rapidocr-onnxruntime",
                        "warning": "No readable text detected in image."
                    }
                # result is list of [box, text, score]
                texts = []
                scores = []
                for item in result:
                    if len(item) >= 3:
                        texts.append(str(item[1]).strip())
                        scores.append(float(item[2]))
                    elif len(item) == 2:
                        texts.append(str(item[0]).strip())
                        scores.append(float(item[1]))

                combined_text = " ".join([t for t in texts if t])
                avg_confidence = sum(scores) / len(scores) if scores else 0.0

                warning = None
                if avg_confidence < 0.60 and combined_text:
                    warning = f"Low OCR extraction confidence ({round(avg_confidence * 100, 1)}%). Some characters or URLs may be distorted."

                return {
                    "text": combined_text.strip(),
                    "confidence": round(avg_confidence, 3),
                    "engine": "rapidocr-onnxruntime",
                    "warning": warning
                }
            except Exception as e:
                logger.warning(f"RapidOCR processing failed, trying fallback: {e}")

        # 2. Try Tesseract as fallback
        try:
            import pytesseract
            from PIL import Image

            # Check known Windows Tesseract locations if not on PATH
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
            ]
            for p in tesseract_paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break

            img = Image.open(file_path)
            # Try getting osd / confidence if possible, or basic text
            text = pytesseract.image_to_string(img)
            text = text.strip() if text else ""

            # Try to get tesseract confidence data
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                avg_conf = (sum(confs) / len(confs) / 100.0) if confs else (0.85 if text else 0.0)
            except Exception:
                avg_conf = 0.85 if text else 0.0

            warning = None
            if not text:
                warning = "No readable text detected in image."
            elif avg_conf < 0.60:
                warning = f"Low OCR extraction confidence ({round(avg_conf * 100, 1)}%)."

            return {
                "text": text,
                "confidence": round(avg_conf, 3),
                "engine": "tesseract",
                "warning": warning
            }
        except Exception as e:
            logger.warning(f"Tesseract fallback failed or unavailable: {e}")

        # If both fail
        raise RuntimeError(
            "OCR screenshot extraction requires an OCR engine. "
            "Please ensure rapidocr-onnxruntime is installed or Tesseract OCR is available."
        )

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        res = cls.extract_text_and_confidence(file_path)
        return res.get("text", "")
