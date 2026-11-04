"""
ShieldAI Single Database Adapter.
Delegates all database access to the canonical SQLite/PostgreSQL layer
in core.database.db_instance. No duplicate storage or in-memory fallback.
"""
from core.database import db_instance
from services.admin_service import AdminService


def is_persistent() -> bool:
    return True


def log_flagged_message(entry: dict) -> str:
    return db_instance.log_message(entry)


def get_stats() -> dict:
    return db_instance.get_stats()


def get_recent(limit: int = 20) -> list:
    return db_instance.get_reports(page=1, page_size=limit).get("reports", [])


def get_all_flagged() -> list:
    return db_instance.get_reports(page=1, page_size=1000).get("reports", [])


def update_flagged_message_cluster(text_preview: str, cluster_id: str) -> None:
    pass


def get_daily_counts(days: int = 30) -> list:
    return db_instance.get_daily_counts(days=days)


def detect_anomalies(daily_counts: list, window: int = 7, z_threshold: float = 2.0) -> list:
    return AdminService.detect_anomalies(daily_counts, window=window, z_threshold=z_threshold)


def log_audit_event(actor: str, action: str, resource: str, detail: dict, status: str = "success", error: str = None):
    return db_instance.log_audit_event(actor, action, resource, detail, status=status, error=error)


def get_audit_log(limit: int = 50) -> list:
    return db_instance.get_audit_log(limit=limit)


def get_chat_session(session_id: str) -> list:
    return db_instance.get_chat_session(session_id)


def save_chat_session(session_id: str, messages: list):
    return db_instance.save_chat_session(session_id, messages)


def get_incident(incident_id: str) -> dict:
    return db_instance.get_incident(incident_id)


def update_incident(incident_id: str, updates: dict) -> bool:
    return db_instance.update_incident(incident_id, updates)


def delete_incident(incident_id: str) -> bool:
    return db_instance.delete_incident(incident_id)


def get_user(username: str) -> dict:
    return db_instance.get_user(username)


def create_user(username: str, password_hash: str, role: str = "User") -> bool:
    return db_instance.create_user(username, password_hash, role)


def seed_mock_data_if_empty():
    db_instance.seed_mock_data_if_empty()


def purge_expired_data(retention_days: int = None) -> dict:
    return db_instance.purge_expired_data(retention_days)
