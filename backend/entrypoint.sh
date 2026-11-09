#!/bin/bash
set -e

echo "Waiting for MongoDB to be ready..."
# A simple python script to check mongo connection
python -c '
import os, sys, time
from pymongo import MongoClient

uri = os.environ.get("MONGODB_URI")
if not uri:
    sys.exit(0) # In-memory fallback mode

client = MongoClient(uri, serverSelectionTimeoutMS=2000)
max_retries = 30
for i in range(max_retries):
    try:
        client.admin.command("ping")
        print("MongoDB is up and running!")
        sys.exit(0)
    except Exception as e:
        print(f"MongoDB not ready yet... (Attempt {i+1}/{max_retries})")
        time.sleep(2)
sys.exit(1)
'

echo "Running idempotent seed script..."
python -c '
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_stats

stats = get_stats()
if stats.get("total_flagged", 0) > 0 or stats.get("total_reports", 0) > 0:
    print("Database already contains data. Skipping seed to prevent duplicates.")
    sys.exit(0)
else:
    print("Database is empty. Running seed_demo_data.py...")
    import subprocess
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_demo_data.py")
    if not os.path.exists(script_path):
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "seed_demo_data.py")
    subprocess.run(["python", script_path])
'

echo "Starting backend server..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
