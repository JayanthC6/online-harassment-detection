from datetime import datetime, timezone, timedelta
from collections import Counter
import math
from core.database import db_instance
from services.behavior_service import BehaviorService

MAX_LOG_ENTRIES = 500

class AdminService:
    @staticmethod
    def log_conversation(entry: dict) -> None:
        entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
        if db_instance.is_persistent:
            db_instance.conversations.insert_one(entry)
        else:
            db_instance.fallback_conversations.insert(0, entry)
            del db_instance.fallback_conversations[MAX_LOG_ENTRIES:]
            
        messages = entry.get("messages", [])
        BehaviorService.log_conversation_incidents(messages)

    @staticmethod
    def log_message(entry: dict) -> None:
        entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
        if db_instance.is_persistent:
            db_instance.collection.insert_one(entry)
        else:
            db_instance.fallback_store.insert(0, entry)
            del db_instance.fallback_store[MAX_LOG_ENTRIES:]
            
        actor_id = entry.get("actor_id")
        BehaviorService.log_incident(actor_id, entry)

    @staticmethod
    def get_stats() -> dict:
        if db_instance.is_persistent:
            total = db_instance.collection.count_documents({})
            safe = db_instance.collection.count_documents({"label": "non_harassing"})
            high_risk = db_instance.collection.count_documents({"risk_score": {"$gte": 75}})
            medium_risk = db_instance.collection.count_documents({"risk_score": {"$gte": 40, "$lt": 75}})
            
            pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
            breakdown = {doc["_id"]: doc["count"] for doc in db_instance.collection.aggregate(pipeline) if doc["_id"]}

            avg_pipeline = [
                {"$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$confidence"},
                    "avg_risk": {"$avg": "$risk_score"}
                }}
            ]
            avgs = list(db_instance.collection.aggregate(avg_pipeline))
            avg_conf = avgs[0]["avg_confidence"] if avgs and avgs[0]["avg_confidence"] is not None else 0
            avg_risk = avgs[0]["avg_risk"] if avgs and avgs[0]["avg_risk"] is not None else 0

            conv_total = db_instance.conversations.count_documents({})
            conv_escalated = db_instance.conversations.count_documents({"escalation_score": {"$gt": 0}})
            
            conv_avg_pipeline = [
                {"$group": {
                    "_id": None,
                    "avg_risk": {"$avg": "$conversation_risk"}
                }}
            ]
            c_avgs = list(db_instance.conversations.aggregate(conv_avg_pipeline))
            conv_avg_risk = c_avgs[0]["avg_risk"] if c_avgs and c_avgs[0]["avg_risk"] is not None else 0

            return {
                "total_reports": total,
                "safe_messages": safe,
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "avg_confidence": round(avg_conf, 3),
                "avg_risk_score": round(avg_risk, 1),
                "category_breakdown": breakdown,
                "conversation_stats": {
                    "total": conv_total,
                    "escalated": conv_escalated,
                    "avg_risk": round(conv_avg_risk, 1)
                }
            }
        else:
            total = len(db_instance.fallback_store)
            safe = sum(1 for e in db_instance.fallback_store if e.get("label") == "non_harassing")
            high_risk = sum(1 for e in db_instance.fallback_store if e.get("risk_score", 0) >= 75)
            medium_risk = sum(1 for e in db_instance.fallback_store if 40 <= e.get("risk_score", 0) < 75)
            breakdown = Counter(e.get("category") for e in db_instance.fallback_store if e.get("category"))
            
            avg_conf = sum(e.get("confidence", 0) for e in db_instance.fallback_store) / total if total > 0 else 0
            avg_risk = sum(e.get("risk_score", 0) for e in db_instance.fallback_store) / total if total > 0 else 0
            
            conv_total = len(db_instance.fallback_conversations)
            conv_escalated = sum(1 for e in db_instance.fallback_conversations if e.get("escalation_score", 0) > 0)
            conv_avg_risk = sum(e.get("conversation_risk", 0) for e in db_instance.fallback_conversations) / conv_total if conv_total > 0 else 0
            
            return {
                "total_reports": total,
                "safe_messages": safe,
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "avg_confidence": round(avg_conf, 3),
                "avg_risk_score": round(avg_risk, 1),
                "category_breakdown": dict(breakdown),
                "conversation_stats": {
                    "total": conv_total,
                    "escalated": conv_escalated,
                    "avg_risk": round(conv_avg_risk, 1)
                }
            }

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
        query = {}
        if search:
            query["text_preview"] = {"$regex": search, "$options": "i"}
        if category:
            query["category"] = category
        if cluster_id:
            query["cluster_id"] = cluster_id
        
        if risk_level:
            if risk_level == "high":
                query["risk_score"] = {"$gte": 75}
            elif risk_level == "medium":
                query["risk_score"] = {"$gte": 40, "$lt": 75}
            elif risk_level == "low":
                query["risk_score"] = {"$lt": 40}
                
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["logged_at"] = date_query

        if db_instance.is_persistent:
            total = db_instance.collection.count_documents(query)
            
            sort_direction = -1 if sort_order == "desc" else 1
            sort_field = "risk_score" if sort_by == "risk" else "confidence" if sort_by == "confidence" else "logged_at"
            
            docs = list(db_instance.collection.find(query, {"_id": 0})
                        .sort(sort_field, sort_direction)
                        .skip((page - 1) * page_size)
                        .limit(page_size))
            
            for doc in docs:
                doc.pop("embedding", None)
                
            return {
                "reports": docs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": math.ceil(total / page_size) if total > 0 else 0
            }
        else:
            filtered = db_instance.fallback_store
            
            if search:
                filtered = [e for e in filtered if search.lower() in e.get("text_preview", "").lower()]
            if category:
                filtered = [e for e in filtered if e.get("category") == category]
            if cluster_id:
                filtered = [e for e in filtered if e.get("cluster_id") == cluster_id]
                
            if risk_level == "high":
                filtered = [e for e in filtered if e.get("risk_score", 0) >= 75]
            elif risk_level == "medium":
                filtered = [e for e in filtered if 40 <= e.get("risk_score", 0) < 75]
            elif risk_level == "low":
                filtered = [e for e in filtered if e.get("risk_score", 0) < 40]
                
            if date_from:
                filtered = [e for e in filtered if e.get("logged_at", "") >= date_from]
            if date_to:
                filtered = [e for e in filtered if e.get("logged_at", "") <= date_to]
                
            sort_field = "risk_score" if sort_by == "risk" else "confidence" if sort_by == "confidence" else "logged_at"
            filtered = sorted(filtered, key=lambda x: x.get(sort_field, 0), reverse=(sort_order == "desc"))
            
            total = len(filtered)
            start_idx = (page - 1) * page_size
            docs = filtered[start_idx : start_idx + page_size]
            
            for doc in docs:
                doc.pop("embedding", None)
                
            return {
                "reports": docs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": math.ceil(total / page_size) if total > 0 else 0
            }

    @staticmethod
    def get_conversations(
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "logged_at",
        sort_order: str = "desc",
    ) -> dict:
        if db_instance.is_persistent:
            total = db_instance.conversations.count_documents({})
            sort_direction = -1 if sort_order == "desc" else 1
            sort_field = "conversation_risk" if sort_by == "risk" else "logged_at"
            
            docs = list(db_instance.conversations.find({}, {"_id": 0})
                        .sort(sort_field, sort_direction)
                        .skip((page - 1) * page_size)
                        .limit(page_size))
            return {
                "conversations": docs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": math.ceil(total / page_size) if total > 0 else 0
            }
        else:
            filtered = db_instance.fallback_conversations
            sort_field = "conversation_risk" if sort_by == "risk" else "logged_at"
            filtered = sorted(filtered, key=lambda x: x.get(sort_field, 0), reverse=(sort_order == "desc"))
            
            total = len(filtered)
            start_idx = (page - 1) * page_size
            docs = filtered[start_idx : start_idx + page_size]
            
            return {
                "conversations": docs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": math.ceil(total / page_size) if total > 0 else 0
            }

    @staticmethod
    def get_analytics() -> dict:
        if not db_instance.is_persistent:
            high = sum(1 for e in db_instance.fallback_store if e.get("risk_score", 0) >= 75)
            medium = sum(1 for e in db_instance.fallback_store if 40 <= e.get("risk_score", 0) < 75)
            low = sum(1 for e in db_instance.fallback_store if e.get("risk_score", 0) < 40)
            
            model_usage = Counter(e.get("model", "unknown") for e in db_instance.fallback_store)
            
            conf_dist = {}
            for e in db_instance.fallback_store:
                c = e.get("confidence", 0)
                bucket = min(math.floor(c / 0.2) * 0.2, 0.8) if c < 1 else 0.8
                key = f"{bucket:.1f}"
                conf_dist[key] = conf_dist.get(key, 0) + 1
                
            label_freq = Counter()
            combinations = Counter()
            for e in db_instance.fallback_store:
                primary = e.get("primary_label", e.get("category", "none"))
                secondary = e.get("secondary_labels", {})
                
                label_freq[primary] += 1
                for sec in secondary.keys():
                    label_freq[sec] += 1
                
                combo = [primary] + list(secondary.keys())
                combo.sort()
                combinations[", ".join(combo)] += 1
            
            top_combinations = dict(combinations.most_common(5))
            
            return {
                "risk_distribution": {"high": high, "medium": medium, "low": low},
                "model_usage": dict(model_usage),
                "confidence_distribution": conf_dist,
                "label_frequency": dict(label_freq),
                "top_combinations": top_combinations
            }
            
        high = db_instance.collection.count_documents({"risk_score": {"$gte": 75}})
        medium = db_instance.collection.count_documents({"risk_score": {"$gte": 40, "$lt": 75}})
        low = db_instance.collection.count_documents({"risk_score": {"$lt": 40}})
        
        model_pipeline = [{"$group": {"_id": "$model", "count": {"$sum": 1}}}]
        model_usage = {doc["_id"] or "unknown": doc["count"] for doc in db_instance.collection.aggregate(model_pipeline)}
        
        conf_pipeline = [
            {"$bucket": {
                "groupBy": "$confidence",
                "boundaries": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                "default": "Other",
                "output": {"count": {"$sum": 1}}
            }}
        ]
        conf_dist = {f"{doc['_id']}": doc["count"] for doc in db_instance.collection.aggregate(conf_pipeline)}
        
        # We also compute the label_frequency and top_combinations purely in python for simplicity since datasets are small for demo
        # Alternatively, we could do a complex mongo pipeline. We'll do a simple find({}) to calculate combos.
        docs = db_instance.collection.find({}, {"primary_label": 1, "category": 1, "secondary_labels": 1})
        label_freq = Counter()
        combinations = Counter()
        
        for e in docs:
            primary = e.get("primary_label", e.get("category", "none"))
            secondary = e.get("secondary_labels", {})
            
            label_freq[primary] += 1
            for sec in secondary.keys():
                label_freq[sec] += 1
            
            combo = [primary] + list(secondary.keys())
            combo.sort()
            combinations[", ".join(combo)] += 1
            
        top_combinations = dict(combinations.most_common(5))
        
        return {
            "risk_distribution": {"high": high, "medium": medium, "low": low},
            "model_usage": model_usage,
            "confidence_distribution": conf_dist,
            "label_frequency": dict(label_freq),
            "top_combinations": top_combinations
        }

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

    # ── Mutating actions ──────────────────────────────────────────────────────

    @staticmethod
    def dismiss_incident(incident_id: str) -> None:
        """Mark an incident as reviewed/dismissed (sets dismissed=True)."""
        if db_instance.is_persistent:
            from bson import ObjectId
            try:
                db_instance.collection.update_one(
                    {"_id": ObjectId(incident_id)},
                    {"$set": {"dismissed": True}},
                )
            except Exception as e:
                raise RuntimeError(f"Could not dismiss incident {incident_id}: {e}")
        else:
            for entry in db_instance.fallback_store:
                if str(entry.get("_id", "")) == incident_id:
                    entry["dismissed"] = True
                    return

    @staticmethod
    def override_classification(incident_id: str, new_label: str) -> None:
        """Override the primary label of an incident."""
        if db_instance.is_persistent:
            from bson import ObjectId
            try:
                db_instance.collection.update_one(
                    {"_id": ObjectId(incident_id)},
                    {"$set": {"primary_label": new_label, "overridden": True}},
                )
            except Exception as e:
                raise RuntimeError(f"Could not override incident {incident_id}: {e}")
        else:
            for entry in db_instance.fallback_store:
                if str(entry.get("_id", "")) == incident_id:
                    entry["primary_label"] = new_label
                    entry["overridden"] = True
                    return

    @staticmethod
    def ban_actor(actor_id: str, reason: str) -> None:
        """Flag all incidents from an actor as banned."""
        if db_instance.is_persistent:
            db_instance.collection.update_many(
                {"actor_id": actor_id},
                {"$set": {"actor_banned": True, "ban_reason": reason}},
            )
        else:
            for entry in db_instance.fallback_store:
                if entry.get("actor_id") == actor_id:
                    entry["actor_banned"] = True
                    entry["ban_reason"] = reason
