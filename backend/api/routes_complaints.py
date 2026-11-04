from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import os
import tempfile
import uuid
from bson.objectid import ObjectId

from api.dependencies import token_required, token_optional, require_role
from services.prediction_service import PredictionService
from services.admin_service import AdminService
from core.database import db_instance

complaints_bp = Blueprint("complaints", __name__)

@complaints_bp.route("/complaints", methods=["POST"])
@complaints_bp.route("/api/complaints", methods=["POST"])
@token_optional
def submit_complaint(token_data=None):
    """Users submit a complaint with text or file evidence."""
    user_id = token_data.get("user") if token_data else "anonymous"
    text = ""
    
    if request.is_json:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
    else:
        text = request.form.get("text", "")

    file = request.files.get("file")
    if file and not text:
        try:
            content = file.read().decode("utf-8", errors="ignore")
            text = content[:2000]
        except Exception:
            text = f"Attached evidence file: {file.filename}"

    if not text.strip():
        return jsonify({"error": "Please provide text or upload a file as evidence."}), 400

    result = PredictionService.classify_text(text)
    result = PredictionService.attach_risk_and_similarity(result, text)
    result["user_id"] = user_id
    result["source"] = "complaint"
    result["status"] = "open"
    result["incident_id"] = str(uuid.uuid4())
    result["logged_at"] = datetime.now(timezone.utc).isoformat()
    
    AdminService.log_message(result)

    return jsonify({
        "success": True,
        "message": "Your complaint has been securely submitted for review.",
        "incident_id": result["incident_id"],
        "result": result
    }), 201

@complaints_bp.route("/history/my", methods=["GET"])
@complaints_bp.route("/api/history/my", methods=["GET"])
@token_required
def get_my_history(token_data):
    """Users view their own analysis history"""
    user_id = token_data.get("user")
    res = db_instance.get_reports(page=1, page_size=100, user_id=user_id, source="self_serve")
    complaints = res.get("reports", [])
    return jsonify({"complaints": complaints})

@complaints_bp.route("/history/<entry_id>", methods=["DELETE"])
@complaints_bp.route("/api/history/<entry_id>", methods=["DELETE"])
@token_required
def delete_history_entry(entry_id, token_data):
    """Users delete their own history entry"""
    user_id = token_data.get("user")
    inc = db_instance.get_incident(entry_id)
    if not inc:
        return jsonify({"error": "Not found"}), 404
    if inc.get("user_id") != user_id and token_data.get("role", "").lower() not in ["admin", "moderator"]:
        return jsonify({"error": "Forbidden: Cannot delete another user's history"}), 403
    db_instance.delete_incident(entry_id)
    return jsonify({"message": "Deleted successfully"})

@complaints_bp.route("/admin/complaints", methods=["GET"])
@complaints_bp.route("/api/admin/complaints", methods=["GET"])
@token_required
@require_role("Admin", "Moderator")
def get_all_complaints(token_data):
    """Analysts view all complaints"""
    complaints = db_instance.get_complaints()
    return jsonify({"complaints": complaints})
