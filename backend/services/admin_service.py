from datetime import datetime, timezone, timedelta
from collections import Counter
import math
from core.database import db_instance

MAX_LOG_ENTRIES = 500

class AdminService:
    @staticmethod
    def log_flagged_message(entry: dict) -> None:
        entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
        if db_instance.is_persistent:
            db_instance.collection.insert_one(entry)
        else:
            db_instance.fallback_store.insert(0, entry)
            del db_instance.fallback_store[MAX_LOG_ENTRIES:]

    @staticmethod
    def get_stats() -> dict:
        if db_instance.is_persistent:
            total = db_instance.collection.count_documents({})
            pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
            breakdown = {doc["_id"]: doc["count"] for doc in db_instance.collection.aggregate(pipeline)}
            return {"total_flagged": total, "category_breakdown": breakdown}
        else:
            breakdown = Counter(e["category"] for e in db_instance.fallback_store)
            return {"total_flagged": len(db_instance.fallback_store), "category_breakdown": dict(breakdown)}

    @staticmethod
    def get_recent(limit: int = 20) -> list:
        limit = min(limit, MAX_LOG_ENTRIES)
        if db_instance.is_persistent:
            docs = list(db_instance.collection.find({}, {"_id": 0}).sort("risk_score", -1).limit(limit))
            return docs
        else:
            sorted_store = sorted(db_instance.fallback_store, key=lambda x: x.get("risk_score", 0), reverse=True)
            return sorted_store[:limit]

    @staticmethod
    def get_all_flagged() -> list:
        if db_instance.is_persistent:
            return list(db_instance.collection.find({}, {"_id": 0}))
        else:
            return list(db_instance.fallback_store)

    @staticmethod
    def update_flagged_message_cluster(text_preview: str, cluster_id: str) -> None:
        if db_instance.is_persistent:
            db_instance.collection.update_many(
                {"text_preview": text_preview},
                {"$set": {"cluster_id": cluster_id}},
            )
        else:
            for entry in db_instance.fallback_store:
                if entry.get("text_preview") == text_preview:
                    entry["cluster_id"] = cluster_id

    @staticmethod
    def get_daily_counts(days: int = 30) -> list:
        now = datetime.now(timezone.utc)
        date_counts = {}

        for i in range(days):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            date_counts[d] = 0

        if db_instance.is_persistent:
            cutoff = (now - timedelta(days=days)).isoformat()
            docs = db_instance.collection.find(
                {"logged_at": {"$gte": cutoff}},
                {"logged_at": 1, "_id": 0}
            )
            for doc in docs:
                d = doc.get("logged_at", "")[:10]
                if d in date_counts:
                    date_counts[d] += 1
        else:
            for entry in db_instance.fallback_store:
                d = entry.get("logged_at", "")[:10]
                if d in date_counts:
                    date_counts[d] += 1

        result = sorted(
            [{"date": k, "count": v} for k, v in date_counts.items()],
            key=lambda x: x["date"]
        )
        return result

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
