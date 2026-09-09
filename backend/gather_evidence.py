import requests
import json
import uuid
import time
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()
client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017"))
db_conn = client["harassment_detection"]
history_collection = db_conn["flagged_messages"]

def gather():
    # 1. Register Public User
    BASE_URL = "http://127.0.0.1:5000"
    
    username_u = f"public_user_{uuid.uuid4().hex[:6]}"
    res_u = requests.post(f"{BASE_URL}/auth/register", json={"username": username_u, "password": "123"})
    token_u = res_u.json().get("token")
    
    # Register Analyst (via direct DB insertion since /auth/register hardcodes User)
    username_a = f"analyst_{uuid.uuid4().hex[:6]}"
    from werkzeug.security import generate_password_hash
    db_conn["users"].insert_one({
        "username": username_a,
        "password_hash": generate_password_hash("123"),
        "role": "Analyst"
    })
    res_a = requests.post(f"{BASE_URL}/admin/login", json={"username": username_a, "password": "123"})
    token_a = res_a.json().get("token")
    
    # 2. Make Requests
    text = "My phone number is 555-1234. I will hurt you."
    
    # Public user request
    res1 = requests.post(f"{BASE_URL}/predict", headers={
        "Origin": "http://127.0.0.1:3000",
        "Authorization": f"Bearer {token_u}"
    }, json={
        "text": text,
        "actor_id": "target_user",
        "persist": True
    })
    print("Public user predict status:", res1.status_code)
    
    # Analyst request
    res2 = requests.post(f"{BASE_URL}/predict", headers={
        "Origin": "http://127.0.0.1:3000",
        "Authorization": f"Bearer {token_a}"
    }, json={
        "text": text,
        "actor_id": "target_user",
        "persist": True
    })
    print("Analyst predict status:", res2.status_code)
    
    time.sleep(1)
    
    # 3. Pull from DB
    doc_u = history_collection.find_one({"user_id": username_u}, sort=[("timestamp", -1)])
    doc_a = history_collection.find_one({"user_id": username_a}, sort=[("timestamp", -1)])
    
    if doc_u: doc_u.pop("_id", None)
    if doc_a: doc_a.pop("_id", None)
    
    print("=== PUBLIC USER RECORD ===")
    print(json.dumps(doc_u, indent=2)) if doc_u else print("None found")
    print("\n=== ANALYST RECORD ===")
    print(json.dumps(doc_a, indent=2)) if doc_a else print("None found")

if __name__ == "__main__":
    gather()
