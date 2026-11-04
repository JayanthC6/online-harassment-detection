from datetime import datetime, timezone, timedelta
from collections import Counter
import math
from core.database import db_instance
from services.behavior_service import BehaviorService

class AdminService:
    @staticmethod
    def log_conversation(entry: dict) -> None:
        entry["logged_at"] = entry.get("logged_at") or datetime.now(timezone.utc).isoformat()
        db_instance.log_conversation(entry)
        messages = entry.get("messages", [])
        if entry.get("source") != "self_serve":
            BehaviorService.log_conversation_incidents(messages)

    @staticmethod
    def log_message(entry: dict) -> None:
        entry["logged_at"] = entry.get("logged_at") or datetime.now(timezone.utc).isoformat()
        db_instance.log_message(entry)
        actor_id = entry.get("actor_id")
        if entry.get("source") != "self_serve":
            BehaviorService.log_incident(actor_id, entry)

    @staticmethod
    def get_stats() -> dict:
        return db_instance.get_stats()

    @staticmethod
    def get_reports(
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "logged_at",
        sort_order: str = "desc",
        search: str = "",
        category: str = "",
        risk_level: str = "",
        date_from: str = "",
        date_to: str = "",
        cluster_id: str = ""
    ) -> dict:
        return db_instance.get_reports(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            category=category,
            risk_level=risk_level
        )

    @staticmethod
    def get_conversations(
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "logged_at",
        sort_order: str = "desc",
    ) -> dict:
        return db_instance.get_conversations(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

    @staticmethod
    def get_analytics() -> dict:
        return db_instance.get_analytics()

    @staticmethod
    def get_all_flagged() -> list:
        res = db_instance.get_reports(page=1, page_size=1000)
        return res.get("reports", [])

    @staticmethod
    def update_flagged_message_cluster(text_preview: str, cluster_id: str) -> None:
        pass

    @staticmethod
    def get_daily_counts(days: int = 30) -> list:
        return db_instance.get_daily_counts(days=days)

    @staticmethod
    def detect_anomalies(daily_counts: list, window: int = 7, z_threshold: float = 2.0) -> list:
        anomalies = []
        counts = [d["count"] for d in daily_counts]

        for i in range(window, len(counts)):
            history = counts[i - window : i]
            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std = math.sqrt(variance) if variance > 0 else 0

            if std == 0:
                if counts[i] > mean + 2:
                    anomalies.append({
                        "date": daily_counts[i]["date"],
                        "count": counts[i],
                        "avg": round(mean, 1),
                        "std": 0.0,
                        "z_score": 99.99,
                    })
                continue

            z_score = (counts[i] - mean) / std
            if z_score > z_threshold:
                anomalies.append({
                    "date": daily_counts[i]["date"],
                    "count": counts[i],
                    "avg": round(mean, 1),
                    "std": round(std, 2),
                    "z_score": round(z_score, 2),
                })

        return anomalies

    # ── Mutating actions ──────────────────────────────────────────────────────

    @staticmethod
    def dismiss_incident(incident_id: str) -> None:
        """Mark an incident as reviewed/dismissed (sets status=dismissed)."""
        rep = db_instance.get_incident(incident_id)
        if not rep:
            raise RuntimeError(f"Incident {incident_id} not found")
        db_instance.update_incident(incident_id, {"status": "dismissed"})
        actor_id = rep.get("actor_id")
        if actor_id:
            from services.email_service import EmailService
            EmailService.send_status_update(actor_id, incident_id, "dismiss")

    @staticmethod
    def override_classification(incident_id: str, new_label: str) -> None:
        """Override the primary label of an incident."""
        rep = db_instance.get_incident(incident_id)
        if not rep:
            raise RuntimeError(f"Incident {incident_id} not found")
        db_instance.update_incident(incident_id, {
            "primary_label": new_label,
            "category": new_label.lower().replace(" ", "_")
        })
        actor_id = rep.get("actor_id")
        if actor_id:
            from services.email_service import EmailService
            EmailService.send_status_update(actor_id, incident_id, "override", {"new_label": new_label})

    @staticmethod
    def ban_actor(actor_id: str, reason: str) -> None:
        """Flag all incidents from an actor as banned."""
        db_instance.ban_actor(actor_id, reason)
