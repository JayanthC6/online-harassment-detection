import sys
import os
import json

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from app import app

client = app.test_client()

# Check /health and /api/health
res = client.get("/api/health")
print(f"HTTP Status: {res.status_code}")
print("Response JSON:")
print(json.dumps(res.get_json(), indent=2))

