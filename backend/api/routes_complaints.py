from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import tempfile

from api.dependencies import token_required, require_role
from services.prediction_service import PredictionService
from ml.ocr import extract_and_classify
import db

complaints_bp = Blueprint("complaints", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "mov", "webm", "ogg"}

@complaints_bp.route("/complaints", methods=["POST"])
@token_required
def create_complaint(token_data):
    """Users submit a complaint (text, image, or audio)"""
    user_id = token_data.get("user")
    
    # Can be multipart/form-data for files or application/json for text
    if request.is_json:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"error": "text is required"}), 400
            
        result = PredictionService.classify_text(text)
        result["text_preview"] = text[:120]
        result["text_full"] = text
        result = PredictionService.attach_risk_and_similarity(result, text)
        result.pop("embedding", None)
        
        complaint_data = {
            "type": "text",
            "content": text,
            "ai_analysis": result
        }
        
    elif "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename."}), 400
            
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                file.save(tmp.name)
                try:
                    result = extract_and_classify(tmp.name, PredictionService.classify_text)
                    extracted_text = result.get("extracted_text", "")
                    result = PredictionService.attach_risk_and_similarity(result, extracted_text)
                    result.pop("embedding", None)
                    complaint_data = {
                        "type": "image",
                        "content": extracted_text,
                        "ai_analysis": result
                    }
                except Exception as e:
                    os.remove(tmp.name)
                    return jsonify({"error": f"OCR/Analysis failed: {str(e)}"}), 500
            os.remove(tmp.name)
            
        elif ext in ALLOWED_AUDIO_EXTENSIONS:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                file.save(tmp.name)
                try:
                    from ml.transcribe import transcribe
                    transcript_data = transcribe(tmp.name)
                    extracted_text = transcript_data["text"]
                    result = PredictionService.classify_text(extracted_text)
                    result = PredictionService.attach_risk_and_similarity(result, extracted_text)
                    result.pop("embedding", None)
                    complaint_data = {
                        "type": "audio",
                        "content": extracted_text,
                        "ai_analysis": result
                    }
                except Exception as e:
                    os.remove(tmp.name)
                    return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            os.remove(tmp.name)
            
        else:
             return jsonify({"error": "Unsupported file type."}), 400
    else:
        return jsonify({"error": "Invalid payload."}), 400

    complaint_id = db.create_complaint(user_id, complaint_data)
    return jsonify({"message": "Complaint submitted successfully", "complaint_id": complaint_id})


@complaints_bp.route("/complaints/my", methods=["GET"])
@token_required
def get_my_complaints(token_data):
    """Users view their own complaints"""
    user_id = token_data.get("user")
    complaints = db.get_complaints_by_user(user_id)
    return jsonify({"complaints": complaints})


@complaints_bp.route("/admin/complaints", methods=["GET"])
@token_required
@require_role("Admin", "Moderator")
def get_all_complaints(token_data):
    """Analysts view all complaints"""
    complaints = db.get_all_complaints()
    return jsonify({"complaints": complaints})
