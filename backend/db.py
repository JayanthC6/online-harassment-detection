"""
Storage layer for flagged messages. Uses MongoDB if configured (via the
MONGODB_URI environment variable), otherwise falls back to an in-memory
list automatically -- so the app keeps working even before you've set up
a database, same pattern as the DistilBERT auto-fallback in app.py.

Set MONGODB_URI in a .env file (see .env.example) to enable persistence.
Without it, flagged messages reset every time the server restarts, exactly
like the original in-memory version.
"""
import os
import math
from datetime import datetime, timezone, timedelta
from collections import Counter

MAX_LOG_ENTRIES = 500

_client = None
_collection = None
_db_enabled = False
_fallback_store = []  # used only if MongoDB isn't configured/reachable


def _try_connect():
    """Attempt a MongoDB connection once, at import time. Never raises --
    logs a clear reason and falls back to in-memory storage instead."""
    global _client, _collection, _db_enabled

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("[db] MONGODB_URI not set -- using in-memory storage (resets on restart).")
        return

    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi

        _client = MongoClient(uri, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")  # fail fast if the connection string is wrong
        db = _client["harassment_detection"]
        _collection = db["flagged_messages"]
        _db_enabled = True
        print("[db] Connected to MongoDB -- flagged messages will persist.")
    except Exception as e:
        print(f"[db] Could not connect to MongoDB ({e}) -- falling back to in-memory storage.")
        _client = None
        _collection = None
        _db_enabled = False


_try_connect()


def is_persistent() -> bool:
    """True if actually backed by MongoDB, False if using the in-memory fallback."""
    return _db_enabled


# ── Risk scoring ──

# Base risk by category, scaled by confidence to produce 0-100 score
CATEGORY_RISK_BASE = {
    "hate_speech": 80,
    "offensive_language": 50,
    "none": 5,
}


def compute_risk_score(category: str, confidence: float) -> float:
    """
    Compute a composite risk score (0-100) from category and confidence.

    Formula: base_score_for_category * confidence
    - hate_speech at 95% confidence → 80 * 0.95 = 76
    - offensive_language at 40% confidence → 50 * 0.4 = 20
    - none at any confidence → ~5
    """
    base = CATEGORY_RISK_BASE.get(category, 5)
    score = base * confidence
    return round(min(100, max(0, score)), 1)


def log_flagged_message(entry: dict) -> None:
    entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
    if _db_enabled:
        _collection.insert_one(entry)
    else:
        _fallback_store.insert(0, entry)
        del _fallback_store[MAX_LOG_ENTRIES:]


def get_stats() -> dict:
    if _db_enabled:
        total = _collection.count_documents({})
        pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
        breakdown = {doc["_id"]: doc["count"] for doc in _collection.aggregate(pipeline)}
        return {"total_flagged": total, "category_breakdown": breakdown}
    else:
        breakdown = Counter(e["category"] for e in _fallback_store)
        return {"total_flagged": len(_fallback_store), "category_breakdown": dict(breakdown)}


def get_recent(limit: int = 20) -> list:
    """Return the most recent flagged messages, sorted by risk_score descending."""
    limit = min(limit, MAX_LOG_ENTRIES)
    if _db_enabled:
        docs = list(_collection.find({}, {"_id": 0}).sort("risk_score", -1).limit(limit))
        return docs
    else:
        sorted_store = sorted(_fallback_store, key=lambda x: x.get("risk_score", 0), reverse=True)
        return sorted_store[:limit]


def get_all_flagged() -> list:
    """Return all flagged messages (for similarity search). Works with both backends."""
    if _db_enabled:
        return list(_collection.find({}, {"_id": 0}))
    else:
        return list(_fallback_store)


def update_flagged_message_cluster(text_preview: str, cluster_id: str) -> None:
    """Attach a cluster_id to a flagged message for duplicate grouping."""
    if _db_enabled:
        _collection.update_many(
            {"text_preview": text_preview},
            {"$set": {"cluster_id": cluster_id}},
        )
    else:
        for entry in _fallback_store:
            if entry.get("text_preview") == text_preview:
                entry["cluster_id"] = cluster_id


# ── Daily counts and anomaly detection ──

def get_daily_counts(days: int = 30) -> list:
    """
    Return daily counts of flagged messages for the last N days.
    Returns list of {"date": "YYYY-MM-DD", "count": int}.
    """
    now = datetime.now(timezone.utc)
    date_counts = {}

    # Initialize all dates with 0
    for i in range(days):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        date_counts[d] = 0

    if _db_enabled:
        cutoff = (now - timedelta(days=days)).isoformat()
        docs = _collection.find(
            {"logged_at": {"$gte": cutoff}},
            {"logged_at": 1, "_id": 0}
        )
        for doc in docs:
            d = doc.get("logged_at", "")[:10]
            if d in date_counts:
                date_counts[d] += 1
    else:
        for entry in _fallback_store:
            d = entry.get("logged_at", "")[:10]
            if d in date_counts:
                date_counts[d] += 1

    # Sort chronologically
    result = sorted(
        [{"date": k, "count": v} for k, v in date_counts.items()],
        key=lambda x: x["date"]
    )
    return result


def detect_anomalies(daily_counts: list, window: int = 7, z_threshold: float = 2.0) -> list:
    """
    Detect anomalous days using z-score against a simple moving average.

    Method: For each day, compute the mean and std of the previous `window` days.
    If the current day's count has a z-score > z_threshold, flag it.

    Justification for z_threshold=2.0:
    - 2σ captures ~97.7% of normal variation
    - Standard choice for anomaly detection in small-N time series
    - Balances sensitivity (catches real spikes) vs specificity (ignores noise)

    NOTE: If insufficient history (< window days), anomaly detection is skipped
    for those days (not enough data to compute a reliable baseline).

    Args:
        daily_counts: list of {"date": str, "count": int}, sorted chronologically
        window: number of previous days to use as baseline
        z_threshold: z-score above which a day is flagged as anomalous

    Returns:
        list of {"date": str, "count": int, "avg": float, "std": float, "z_score": float}
    """
    anomalies = []
    counts = [d["count"] for d in daily_counts]

    for i in range(window, len(counts)):
        history = counts[i - window : i]
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance) if variance > 0 else 0

        if std == 0:
            # If std is 0 (all same values), flag only if current is notably higher
            if counts[i] > mean + 2:
                anomalies.append({
                    "date": daily_counts[i]["date"],
                    "count": counts[i],
                    "avg": round(mean, 1),
                    "std": 0.0,
                    "z_score": float("inf"),
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