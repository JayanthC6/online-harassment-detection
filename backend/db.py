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
from datetime import datetime, timezone
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
    limit = min(limit, MAX_LOG_ENTRIES)
    if _db_enabled:
        docs = list(_collection.find({}, {"_id": 0}).sort("logged_at", -1).limit(limit))
        return docs
    else:
        return _fallback_store[:limit]