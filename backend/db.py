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
        import certifi
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi

        _client = MongoClient(uri, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        _client.admin.command("ping")  # fail fast if the connection string is wrong
        db = _client["harassment_detection"]
        _collection = db["flagged_messages"]
        _db_enabled = True
        print("[db] Connected to MongoDB -- flagged messages will persist.")
    except Exception as e:
        print("\n" + "!"*60)
        print("WARNING: MONGODB CONNECTION FAILED")
        print("!"*60)
        print(f"Error: {e}")
        print("Falling back to IN-MEMORY storage. All data will be LOST on restart.")
        print("!"*60 + "\n")
        _client = None
        _collection = None
        _db_enabled = False


_try_connect()

def seed_mock_data_if_empty():
    """Auto-seed sample data if the db (or in-memory store) is empty."""
    if os.environ.get("SEED_DEMO_DATA", "").lower() != "true":
        return
        
    stats = get_stats()
    if stats.get("total_flagged", 0) > 0:
        return
        
    print("[db] SEED_DEMO_DATA=true and database is empty. Seeding 15 sample incidents.")
    samples = [
        {"text": "I will kill you and your family, I know where you live", "actor_id": "angry_user_99"}, 
        {"text": "You are a stupid idiot and nobody likes you", "actor_id": "troll_master"}, 
        {"text": "I am going to release those photos of you if you don't pay me $1000", "actor_id": "anon_hacker"}, 
        {"text": "Your account has been suspended. Please click here to verify your identity.", "actor_id": "support_scam"}, 
        {"text": "Invest in this new crypto coin, guaranteed 100x return in 2 days", "actor_id": "crypto_bro"}, 
        {"text": "Send bobs and vagene", "actor_id": "creep_123"}, 
        {"text": "Kill yourself now", "actor_id": "hater_x"}, 
        {"text": "I'm going to track your IP and swat your house", "actor_id": "angry_gamer"}, 
        {"text": "You're a disgusting pig", "actor_id": "troll_master"}, 
        {"text": "I hate people of your kind, you should all be deported", "actor_id": "racist_dude"}, 
        {"text": "Hello how are you doing today?", "actor_id": "friendly_bot"}, 
        {"text": "Please send me your social security number to claim your prize.", "actor_id": "scammer_1"}, 
        {"text": "Give me your lunch money or else I will beat you up", "actor_id": "bully_kid"}, 
        {"text": "I have hacked your webcam and have a video of you. Send 0.1 BTC to this address.", "actor_id": "anon_hacker"}, 
        {"text": "Go back to your country you freak", "actor_id": "racist_dude"}
    ]
    
    # We can't use PredictionService directly here because db is loaded first.
    # Instead, we just manually inject them with pre-computed labels.
    from datetime import datetime, timezone
    
    precomputed = [
        {"primary_label": "Threat", "risk_score": 92.5, "severity_tier": "Critical", "category": "threat"},
        {"primary_label": "Cyberbullying", "risk_score": 65.0, "severity_tier": "High", "category": "cyberbullying"},
        {"primary_label": "Extortion", "risk_score": 88.0, "severity_tier": "Critical", "category": "extortion"},
        {"primary_label": "Phishing", "risk_score": 85.0, "severity_tier": "High", "category": "phishing"},
        {"primary_label": "Scam", "risk_score": 82.0, "severity_tier": "High", "category": "scam"},
        {"primary_label": "Sexual Harassment", "risk_score": 75.0, "severity_tier": "High", "category": "sexual_harassment"},
        {"primary_label": "Self Harm", "risk_score": 95.0, "severity_tier": "Critical", "category": "self_harm"},
        {"primary_label": "Threat", "risk_score": 89.0, "severity_tier": "Critical", "category": "threat"},
        {"primary_label": "Toxicity", "risk_score": 55.0, "severity_tier": "Medium", "category": "toxicity"},
        {"primary_label": "Hate Speech", "risk_score": 78.0, "severity_tier": "High", "category": "hate_speech"},
        {"primary_label": "Clean", "risk_score": 5.0, "severity_tier": "Low", "category": "none"},
        {"primary_label": "Scam", "risk_score": 81.0, "severity_tier": "High", "category": "scam"},
        {"primary_label": "Extortion", "risk_score": 86.0, "severity_tier": "Critical", "category": "extortion"},
        {"primary_label": "Blackmail", "risk_score": 91.0, "severity_tier": "Critical", "category": "blackmail"},
        {"primary_label": "Hate Speech", "risk_score": 76.0, "severity_tier": "High", "category": "hate_speech"}
    ]
    
    for i, item in enumerate(samples):
        entry = {
            "text_preview": item["text"][:120],
            "actor_id": item["actor_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **precomputed[i]
        }
        log_flagged_message(entry)


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
                    "z_score": 99.99,  # std=0, count spiked
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

# Seed mock data automatically on startup if database is empty
seed_mock_data_if_empty()