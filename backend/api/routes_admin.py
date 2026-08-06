from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from services.admin_service import AdminService
from services.behavior_service import BehaviorService
from core.exceptions import AppException

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/stats", methods=["GET"])
def admin_stats():
    from services.prediction_service import PredictionService
    stats = AdminService.get_stats()
    stats["model"] = PredictionService.get_active_model_name()
    return jsonify(stats)

@admin_bp.route("/admin/reports", methods=["GET"])
def admin_reports():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    sort_by = request.args.get("sort_by", "logged_at")
    sort_order = request.args.get("sort_order", "desc")
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    risk_level = request.args.get("risk_level", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    cluster_id = request.args.get("cluster_id", "")
    
    reports_data = AdminService.get_reports(
        page, page_size, sort_by, sort_order, search, 
        category, risk_level, date_from, date_to, cluster_id
    )
    return jsonify(reports_data)

@admin_bp.route("/admin/analytics", methods=["GET"])
def admin_analytics():
    return jsonify(AdminService.get_analytics())

@admin_bp.route("/admin/daily_counts", methods=["GET"])
def admin_daily_counts():
    days = int(request.args.get("days", 30))
    counts = AdminService.get_daily_counts(days=days)
    anomalies = AdminService.detect_anomalies(counts, window=7, z_threshold=2.0)
    return jsonify({
        "counts": counts,
        "anomalies": anomalies
    })

@admin_bp.route("/admin/conversations", methods=["GET"])
def admin_conversations():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    sort_by = request.args.get("sort_by", "logged_at")
    sort_order = request.args.get("sort_order", "desc")
    
    conversations_data = AdminService.get_conversations(
        page, page_size, sort_by, sort_order
    )
    return jsonify(conversations_data)

@admin_bp.route("/admin/profiles", methods=["GET"])
def admin_profiles():
    profiles = BehaviorService.get_all_profiles()
    return jsonify({"profiles": profiles})

