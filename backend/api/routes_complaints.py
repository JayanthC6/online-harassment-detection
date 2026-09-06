from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import tempfile
from bson.objectid import ObjectId

from api.dependencies import token_required, require_role
from services.prediction_service import PredictionService
from services.admin_service import AdminService
from core.database import db_instance

complaints_bp = Blueprint("complaints", __name__)

@complaints_bp.route("/history/my", methods=["GET"])
@token_required
def get_my_history(token_data):
    """Users view their own analysis history"""
    user_id = token_data.get("user")
    if db_instance.is_persistent:
        complaints = list(db_instance.collection.find({"actor_id": user_id, "source": "self_serve"}, {"_id": 1, "logged_at": 1, "text_preview": 1, "primary_label": 1, "confidence": 1, "risk_score": 1, "severity_tier": 1, "category": 1, "actor_id": 1, "source": 1}).sort("logged_at", -1))
        # Convert ObjectId to string for JSON serialization
        for c in complaints:
            if "_id" in c:
                c["_id"] = str(c["_id"])
    else:
        complaints = [c for c in db_instance.fallback_store if c.get("actor_id") == user_id and c.get("source") == "self_serve"]
    return jsonify({"complaints": complaints})

@complaints_bp.route("/history/<entry_id>", methods=["DELETE"])
@token_required
def delete_history_entry(entry_id, token_data):
    """Users delete their own history entry"""
    user_id = token_data.get("user")
    
    if db_instance.is_persistent:
        try:
            doc = db_instance.collection.find_one({"_id": ObjectId(entry_id)})
        except Exception:
            return jsonify({"error": "Invalid ID format"}), 400
            
        if not doc:
            return jsonify({"error": "Not found"}), 404
            
        if doc.get("actor_id") != user_id:
            return jsonify({"error": "Forbidden: Cannot delete another user's history"}), 403
            
        db_instance.collection.delete_one({"_id": ObjectId(entry_id)})
        return jsonify({"message": "Deleted successfully"})
    else:
        # Fallback store
        for i, doc in enumerate(db_instance.fallback_store):
            # In fallback store, we don't have _id (unless added manually), we might match by something else.
            # But wait, fallback store doesn't have _id strings properly assigned, maybe we should just simulate it or match by index/timestamp.
            if str(doc.get("_id", i)) == entry_id:
                if doc.get("actor_id") != user_id:
                    return jsonify({"error": "Forbidden: Cannot delete another user's history"}), 403
                del db_instance.fallback_store[i]
                return jsonify({"message": "Deleted successfully"})
        return jsonify({"error": "Not found"}), 404

@complaints_bp.route("/admin/complaints", methods=["GET"])
@token_required
@require_role("Admin", "Moderator")
def get_all_complaints(token_data):
    """Analysts view all complaints (left intact as per requirements, but hidden in UI)"""
    if db_instance.is_persistent:
        complaints = list(db_instance.collection.find({"source": {"$ne": "self_serve"}}, {"_id": 0}).sort("logged_at", -1))
    else:
        complaints = [c for c in db_instance.fallback_store if c.get("source") != "self_serve"]
    return jsonify({"complaints": complaints})
