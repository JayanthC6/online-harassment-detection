from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from services.admin_service import AdminService
from core.exceptions import AppException
from api.dependencies import token_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing credentials"}), 400
        
    try:
        token = AuthService.authenticate(data["username"], data["password"])
        return jsonify({"token": token})
    except AppException as e:
        return jsonify(e.to_dict()), e.status_code

@admin_bp.route("/admin/stats", methods=["GET"])
@token_required
def admin_stats():
    from services.prediction_service import PredictionService
    stats = AdminService.get_stats()
    stats["model"] = PredictionService.get_active_model_name()
    return jsonify(stats)

@admin_bp.route("/admin/recent", methods=["GET"])
@token_required
def admin_recent():
    limit = int(request.args.get("limit", 20))
    recent = AdminService.get_recent(limit)
    for r in recent:
        r.pop("embedding", None)
    return jsonify(recent)

@admin_bp.route("/admin/daily_counts", methods=["GET"])
@token_required
def admin_daily_counts():
    days = int(request.args.get("days", 30))
    counts = AdminService.get_daily_counts(days=days)
    anomalies = AdminService.detect_anomalies(counts, window=7, z_threshold=2.0)
    return jsonify({
        "counts": counts,
        "anomalies": anomalies
    })
