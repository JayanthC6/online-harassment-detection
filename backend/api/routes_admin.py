"""
Admin API routes — ALL endpoints require a valid JWT.

Authentication:    @token_required  → 401 on missing/invalid token
Authorization:     @require_role()  → 403 on valid token with insufficient role

Role matrix:
    Read endpoints (GET)          → Admin, Moderator, Viewer
    Mutating endpoints (POST)     → Admin, Moderator  (ban actor: Admin only)
    /admin/login                  → public (issues the token)
    /admin/audit                  → Admin only
"""
from flask import Blueprint, request, jsonify, current_app
from services.auth_service import AuthService
from services.admin_service import AdminService
from services.behavior_service import BehaviorService
from core.exceptions import AppException
from api.dependencies import token_required, require_role
import db

admin_bp = Blueprint("admin", __name__)


# ── Authentication ────────────────────────────────────────────────────────────

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """Public — issues a JWT. No token needed to reach this endpoint."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    try:
        token = AuthService.authenticate(username, password)
        return jsonify({"token": token})
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code


# ── Read-only admin endpoints (Admin | Moderator | Viewer) ────────────────────

@admin_bp.route("/admin/stats", methods=["GET"])
@token_required
def admin_stats(token_data):
    from services.prediction_service import PredictionService
    stats = AdminService.get_stats()
    stats["model"] = PredictionService.get_active_model_name()
    return jsonify(stats)


@admin_bp.route("/admin/reports", methods=["GET"])
@token_required
def admin_reports(token_data):
    page        = int(request.args.get("page", 1))
    page_size   = int(request.args.get("page_size", 20))
    sort_by     = request.args.get("sort_by", "logged_at")
    sort_order  = request.args.get("sort_order", "desc")
    search      = request.args.get("search", "")
    category    = request.args.get("category", "")
    risk_level  = request.args.get("risk_level", "")
    date_from   = request.args.get("date_from", "")
    date_to     = request.args.get("date_to", "")
    cluster_id  = request.args.get("cluster_id", "")

    reports_data = AdminService.get_reports(
        page, page_size, sort_by, sort_order, search,
        category, risk_level, date_from, date_to, cluster_id
    )
    return jsonify(reports_data)


@admin_bp.route("/admin/analytics", methods=["GET"])
@token_required
def admin_analytics(token_data):
    return jsonify(AdminService.get_analytics())


@admin_bp.route("/admin/daily_counts", methods=["GET"])
@token_required
def admin_daily_counts(token_data):
    days = int(request.args.get("days", 30))
    counts    = AdminService.get_daily_counts(days=days)
    anomalies = AdminService.detect_anomalies(counts, window=7, z_threshold=2.0)
    return jsonify({"counts": counts, "anomalies": anomalies})


@admin_bp.route("/admin/conversations", methods=["GET"])
@token_required
def admin_conversations(token_data):
    page       = int(request.args.get("page", 1))
    page_size  = int(request.args.get("page_size", 20))
    sort_by    = request.args.get("sort_by", "logged_at")
    sort_order = request.args.get("sort_order", "desc")

    conversations_data = AdminService.get_conversations(page, page_size, sort_by, sort_order)
    return jsonify(conversations_data)


@admin_bp.route("/admin/profiles", methods=["GET"])
@token_required
def admin_profiles(token_data):
    profiles = BehaviorService.get_all_profiles()
    return jsonify({"profiles": profiles})


@admin_bp.route("/admin/audit", methods=["GET"])
@token_required
@require_role("Admin")
def admin_audit_log(token_data):
    """Return recent audit events. Admin-only."""
    limit = int(request.args.get("limit", 200))
    return jsonify({"audit_log": db.get_audit_log(limit=limit)})


# ── Mutating endpoints (Admin | Moderator) ────────────────────────────────────

@admin_bp.route("/admin/incidents/<incident_id>/dismiss", methods=["POST"])
@token_required
@require_role("Admin", "Moderator")
def dismiss_incident(incident_id, token_data):
    """Mark an incident as reviewed/dismissed."""
    actor = token_data.get("user", "unknown")
    detail = {"note": request.get_json(silent=True) or {}}

    try:
        AdminService.dismiss_incident(incident_id)
        db.log_audit_event(actor=actor, action="dismiss_incident", resource=incident_id, detail=detail, status="success")
        return jsonify({"status": "dismissed", "incident_id": incident_id})
    except RuntimeError as e:
        msg = str(e)
        code = 400 if "not a valid ObjectId" in msg else 500
        db.log_audit_event(actor=actor, action="dismiss_incident", resource=incident_id, detail=detail, status="failed", error=msg)
        return jsonify({"error": msg}), code
    except Exception as e:
        db.log_audit_event(actor=actor, action="dismiss_incident", resource=incident_id, detail=detail, status="failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/incidents/<incident_id>/override", methods=["POST"])
@token_required
@require_role("Admin", "Moderator")
def override_classification(incident_id, token_data):
    """Override the classification label of an incident."""
    actor = token_data.get("user", "unknown")
    data  = request.get_json(silent=True) or {}
    new_label = data.get("label", "").strip()

    if not new_label:
        return jsonify({"error": "'label' is required"}), 400

    detail = {"new_label": new_label}

    try:
        AdminService.override_classification(incident_id, new_label)
        db.log_audit_event(actor=actor, action="override_classification", resource=incident_id, detail=detail, status="success")
        return jsonify({"status": "overridden", "incident_id": incident_id, "new_label": new_label})
    except RuntimeError as e:
        msg = str(e)
        code = 400 if "not a valid ObjectId" in msg else 500
        db.log_audit_event(actor=actor, action="override_classification", resource=incident_id, detail=detail, status="failed", error=msg)
        return jsonify({"error": msg}), code
    except Exception as e:
        db.log_audit_event(actor=actor, action="override_classification", resource=incident_id, detail=detail, status="failed", error=str(e))
        return jsonify({"error": str(e)}), 500


# ── Mutating endpoints (Admin ONLY) ──────────────────────────────────────────

@admin_bp.route("/admin/actors/<actor_id>/ban", methods=["POST"])
@token_required
@require_role("Admin")
def ban_actor(actor_id, token_data):
    """Ban an actor (restricts their ability to send messages)."""
    actor = token_data.get("user", "unknown")
    data  = request.get_json(silent=True) or {}
    reason = data.get("reason", "Violated terms of service").strip()

    detail = {"reason": reason}

    try:
        AdminService.ban_actor(actor_id, reason)
        db.log_audit_event(actor=actor, action="ban_actor", resource=actor_id, detail=detail, status="success")
        return jsonify({"status": "banned", "actor_id": actor_id, "reason": reason})
    except Exception as e:
        db.log_audit_event(actor=actor, action="ban_actor", resource=actor_id, detail=detail, status="failed", error=str(e))
        return jsonify({"error": str(e)}), 500
