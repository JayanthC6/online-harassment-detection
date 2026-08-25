from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import tempfile

from api.dependencies import token_required, require_role
from services.prediction_service import PredictionService
from services.admin_service import AdminService
from ml.ocr import extract_and_classify
from core.database import db_instance

complaints_bp = Blueprint("complaints", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "mov", "webm", "ogg"}

from extensions import limiter

@complaints_bp.route("/complaints", methods=["POST"])
@token_required
@limiter.limit("10 per minute")
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
                    result = {**result, "text_preview": extracted_text[:120], "text_full": extracted_text}
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
                    result = {**result, "text_preview": extracted_text[:120], "text_full": extracted_text}
                except Exception as e:
                    os.remove(tmp.name)
                    return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            os.remove(tmp.name)
            
        else:
             return jsonify({"error": "Unsupported file type."}), 400
    else:
        return jsonify({"error": "Invalid payload."}), 400

    entry = {
        "actor_id": user_id,
        "source": "user_complaint",
        **complaint_data,
        **result
    }
    
    # Generate suggested action using the summarize endpoint logic
    try:
        from ml.summarize import summarize_complaint
        cat = result.get("primary_label", result.get("category", "none"))
        conf = result.get("confidence", 0)
        risk = result.get("risk_score", 0)
        summary = summarize_complaint(entry.get("text_full", ""), cat, conf, risk_score=risk, persona="user")
        entry["user_guidance"] = summary.get("suggested_action", "")
        entry["severity_tier"] = summary.get("severity", "Low")
        entry["incident_description"] = summary.get("incident_description", "")
    except Exception as e:
        print(f"Failed to generate guidance: {e}")
        entry["user_guidance"] = ""
        entry["severity_tier"] = "Low"
        entry["incident_description"] = ""

    AdminService.log_message(entry)
    
    # Retrieve the _id generated by log_message if available
    complaint_id = str(entry.get("_id", "unknown"))
    return jsonify({"message": "Complaint submitted successfully", "complaint_id": complaint_id})


@complaints_bp.route("/complaints/my", methods=["GET"])
@token_required
def get_my_complaints(token_data):
    """Users view their own complaints"""
    user_id = token_data.get("user")
    if db_instance.is_persistent:
        complaints = list(db_instance.collection.find({"actor_id": user_id, "source": "user_complaint"}, {"_id": 0}).sort("logged_at", -1))
    else:
        complaints = [c for c in db_instance.fallback_store if c.get("actor_id") == user_id and c.get("source") == "user_complaint"]
    return jsonify({"complaints": complaints})


@complaints_bp.route("/admin/complaints", methods=["GET"])
@token_required
@require_role("Admin", "Moderator")
def get_all_complaints(token_data):
    """Analysts view all complaints"""
    if db_instance.is_persistent:
        complaints = list(db_instance.collection.find({"source": "user_complaint"}, {"_id": 0}).sort("logged_at", -1))
    else:
        complaints = [c for c in db_instance.fallback_store if c.get("source") == "user_complaint"]
    return jsonify({"complaints": complaints})
