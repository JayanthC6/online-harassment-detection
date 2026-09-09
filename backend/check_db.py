import os
from pymongo import MongoClient
import json
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017"))
db = client["harassment_detection"]

def get_latest():
    docs = list(db["flagged_messages"].find().sort("logged_at", -1).limit(5))
    for d in docs:
        d.pop("_id", None)
    
    with open("evidence_output.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)

if __name__ == "__main__":
    get_latest()
