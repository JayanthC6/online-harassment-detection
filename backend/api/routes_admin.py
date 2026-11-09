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
@require_role("Admin", "Moderator", "Viewer")
def admin_stats(token_data):
    from services.prediction_service import PredictionService
    stats = AdminService.get_stats()
    stats["model"] = PredictionService.get_active_model_name()
    stats["model_loaded"] = PredictionService.is_model_loaded()
    stats["mode"] = "hybrid" if stats["model_loaded"] else "rules-only"
    return jsonify(stats)


@admin_bp.route("/admin/reports", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
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
@require_role("Admin", "Moderator", "Viewer")
def admin_analytics(token_data):
    return jsonify(AdminService.get_analytics())


@admin_bp.route("/admin/daily_counts", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
def admin_daily_counts(token_data):
    days = int(request.args.get("days", 30))
    counts    = AdminService.get_daily_counts(days=days)
    anomalies = AdminService.detect_anomalies(counts, window=7, z_threshold=2.0)
    return jsonify({"counts": counts, "anomalies": anomalies})


@admin_bp.route("/admin/conversations", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
def admin_conversations(token_data):
    page       = int(request.args.get("page", 1))
    page_size  = int(request.args.get("page_size", 20))
    sort_by    = request.args.get("sort_by", "logged_at")
    sort_order = request.args.get("sort_order", "desc")

    conversations_data = AdminService.get_conversations(page, page_size, sort_by, sort_order)
    return jsonify(conversations_data)


@admin_bp.route("/admin/profiles", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
def admin_profiles(token_data):
    profiles = BehaviorService.get_all_profiles()
    return jsonify({"profiles": profiles})


# ── Repeat Offenders (Admin | Moderator | Viewer) ───────────────────────────

@admin_bp.route("/admin/offenders", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
def admin_offenders(token_data):
    entity_type = request.args.get("entity_type", "all")
    min_risk = float(request.args.get("min_risk", 0.0))
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "hit_count")
    sort_order = request.args.get("sort_order", "desc")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))

    from services.offender_service import OffenderService
    result = OffenderService.get_offenders(
        entity_type=entity_type,
        min_risk=min_risk,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    return jsonify(result)


@admin_bp.route("/admin/offenders/<path:entity_value>", methods=["GET"])
@token_required
@require_role("Admin", "Moderator", "Viewer")
def admin_offender_detail(entity_value, token_data):
    from services.offender_service import OffenderService
    offender = OffenderService.get_offender_by_value(entity_value)
    if not offender:
        return jsonify({"error": f"Offender '{entity_value}' not found"}), 404
    return jsonify({"offender": offender})


@admin_bp.route("/admin/offenders/<path:entity_value>/status", methods=["POST"])
@token_required
@require_role("Admin", "Moderator")
def admin_update_offender_status(entity_value, token_data):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip().lower()
    notes = data.get("notes", "")
    if new_status not in {"active", "flagged", "banned", "monitored", "cleared"}:
        return jsonify({"error": "Invalid status. Allowed: active, flagged, banned, monitored, cleared"}), 400

    from services.offender_service import OffenderService
    success = OffenderService.update_offender_status(entity_value, new_status, notes)
    if not success:
        return jsonify({"error": f"Offender '{entity_value}' not found or could not be updated"}), 404

    actor = token_data.get("user", "unknown")
    db.log_audit_event(
        actor=actor,
        action="update_offender_status",
        resource=entity_value,
        detail={"status": new_status, "notes": notes},
        status="success"
    )
    return jsonify({"status": "updated", "entity_value": entity_value, "new_status": new_status})


# ── Report & Incident Status Updates ────────────────────────────────────────

@admin_bp.route("/admin/reports/<report_id>/status", methods=["POST", "PATCH"])
@admin_bp.route("/admin/incidents/<report_id>/status", methods=["POST", "PATCH"])
@token_required
@require_role("Admin", "Moderator")
def update_report_status(report_id, token_data):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip().lower()
    allowed_statuses = {"open", "reviewing", "resolved", "dismissed"}
    if new_status not in allowed_statuses:
        return jsonify({"error": f"Invalid status '{new_status}'. Allowed: {sorted(list(allowed_statuses))}"}), 400

    rep = db.get_incident(report_id)
    if not rep:
        return jsonify({"error": f"Report '{report_id}' not found"}), 404

    db.update_incident(report_id, {"status": new_status})
    actor = token_data.get("user", "unknown")
    db.log_audit_event(
        actor=actor,
        action="update_report_status",
        resource=report_id,
        detail={"status": new_status, "note": data.get("note", "")},
        status="success"
    )
    return jsonify({"status": "updated", "report_id": report_id, "new_status": new_status})


@admin_bp.route("/admin/status", methods=["POST"])
@token_required
@require_role("Admin", "Moderator")
def update_status_generic(token_data):
    """Generic status update accepting report_id or incident_id in body."""
    data = request.get_json(silent=True) or {}
    report_id = data.get("id") or data.get("report_id") or data.get("incident_id")
    new_status = (data.get("status") or "").strip().lower()
    if not report_id:
        return jsonify({"error": "Report ID ('id' or 'report_id') is required"}), 400

    allowed_statuses = {"open", "reviewing", "resolved", "dismissed"}
    if new_status not in allowed_statuses:
        return jsonify({"error": f"Invalid status '{new_status}'. Allowed: {sorted(list(allowed_statuses))}"}), 400

    rep = db.get_incident(report_id)
    if not rep:
        return jsonify({"error": f"Report '{report_id}' not found"}), 404

    db.update_incident(report_id, {"status": new_status})
    actor = token_data.get("user", "unknown")
    db.log_audit_event(
        actor=actor,
        action="update_status",
        resource=report_id,
        detail={"status": new_status, "note": data.get("note", "")},
        status="success"
    )
    return jsonify({"status": "updated", "report_id": report_id, "new_status": new_status})


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


@admin_bp.route("/admin/purge", methods=["POST"])
@token_required
@require_role("Admin")
def purge_expired_records(token_data):
    """Purge records older than retention period. Admin only."""
    actor = token_data.get("user", "unknown")
    data = request.get_json(silent=True) or {}
    days = data.get("days")
    if days is not None:
        try:
            days = int(days)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid days parameter"}), 400

    result = db.purge_expired_data(retention_days=days)
    db.log_audit_event(actor=actor, action="purge_expired_records", resource="database", detail={"result": result}, status="success")
    return jsonify(result)
