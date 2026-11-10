"""
ShieldAI OCR Test Suite (Item 4)
Tests with generated images:
- Phishing text
- Abusive text
- Rotated text
- Low-contrast text
- Blank image (no text found, confidence 0.0, never 'safe')
"""
import io
import os
import pytest
from PIL import Image, ImageDraw, ImageFont
from services.ocr_service import OCRService
from ml.ocr import extract_and_classify, extract_text


def _create_text_image(text: str, size=(450, 100), bg_color=(255, 255, 255), text_color=(0, 0, 0), rotate_deg=0) -> str:
    """Helper to render synthetic text image and save to a temporary file."""
    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)
    # Draw simple readable text
    draw.text((15, 25), text, fill=text_color)
    if rotate_deg != 0:
        img = img.rotate(rotate_deg, expand=True, fillcolor=bg_color)
    
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    img.save(tmp.name, format="PNG")
    return tmp.name


def test_ocr_phishing_image():
    phishing_text = "Urgent: Your SBI account is suspended. Verify KYC at http://sbi-kyc-verify.com"
    img_path = _create_text_image(phishing_text, size=(650, 100))
    try:
        res = extract_and_classify(img_path)
        extracted = res.get("extracted_text", "").lower()
        # Verify text was extracted by offline engine
        assert "sbi" in extracted or "kyc" in extracted or "account" in extracted
        assert res.get("level") in ["high", "critical", "medium"]
        assert res.get("category") in ["phishing", "scam"]
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def test_ocr_abusive_image():
    abusive_text = "You are a disgusting idiot go die"
    img_path = _create_text_image(abusive_text, size=(500, 100))
    try:
        res = extract_and_classify(img_path)
        extracted = res.get("extracted_text", "").lower()
        assert "disgusting" in extracted or "idiot" in extracted or "die" in extracted
        assert res.get("level") in ["medium", "high", "critical"]
        assert res.get("label") != "clean"
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def test_ocr_rotated_image():
    text = "Orientation test message for ShieldAI OCR engine"
    img_path = _create_text_image(text, size=(500, 100), rotate_deg=15)
    try:
        meta = OCRService.extract_text_and_confidence(img_path)
        # Should execute without error; confidence score must be numeric
        assert isinstance(meta.get("confidence"), float)
        assert meta.get("engine") in ["rapidocr-onnxruntime", "tesseract"]
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def test_ocr_low_contrast_image():
    text = "Low contrast faint text warning verification"
    # Light gray on white
    img_path = _create_text_image(text, size=(550, 100), bg_color=(255, 255, 255), text_color=(220, 220, 220))
    try:
        meta = OCRService.extract_text_and_confidence(img_path)
        assert isinstance(meta.get("confidence"), float)
        # If confidence is low or text unreadable, warning must be present or text empty
        if meta.get("confidence") < 0.60:
            assert meta.get("warning") is not None
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def test_ocr_blank_image():
    """Blank image must return 'no text found' with confidence 0.0 and NEVER 'safe' or clean."""
    img = Image.new("RGB", (300, 150), color=(255, 255, 255))
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    img.save(tmp.name, format="PNG")
    try:
        res = extract_and_classify(tmp.name)
        assert res.get("level") == "no_text_found"
        assert res.get("label") == "no_text_found"
        assert res.get("extracted_text") == ""
        assert res.get("confidence") == 0.0
        assert "no text" in res.get("warning", "").lower() or "no readable text" in res.get("warning", "").lower()
        # Invariant: must NEVER be classified as 'safe' or 'clean'
        assert res.get("level") != "safe"
        assert res.get("label") != "safe"
        assert res.get("label") != "clean"
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def test_predict_screenshot_endpoint_blank_and_text(client):
    """API endpoint /predict/screenshot handles blank images and text images cleanly."""
    # 1. Blank image -> returns 200 with no_text_found payload
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    data = {"file": (buf, "blank.png")}
    res = client.post("/predict/screenshot", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data.get("label") == "no_text_found"
    assert json_data.get("confidence") == 0.0

    # 2. Phishing image -> returns 200 with threat
    phish_path = _create_text_image("Your SBI netbanking KYC is expired. Click http://sbi-update.xyz immediately")
    try:
        with open(phish_path, "rb") as f:
            data_phish = {"file": (f, "phishing.png")}
            res_phish = client.post("/predict/screenshot", data=data_phish, content_type="multipart/form-data")
            assert res_phish.status_code == 200
            p_data = res_phish.get_json()
            assert p_data.get("threat_score", 0) >= 50.0 or p_data.get("risk_score", 0) >= 50.0
            assert p_data.get("category") in ["phishing", "scam"]
    finally:
        if os.path.exists(phish_path):
            os.remove(phish_path)
