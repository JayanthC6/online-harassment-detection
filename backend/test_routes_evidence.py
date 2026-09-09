"""
Evidence collection script — runs all 8 /predict routes and saves evidence_plan presence
for the Stage 2 review. Outputs a clean summary to evidence_routes.json.
"""
import requests
import json
import os

BASE = "http://127.0.0.1:5000"
HEADERS = {"Origin": "http://127.0.0.1:3000"}
THREAT_TEXT = "I will kill you. I know where you live. Pay me $5000 or else."

results = {}

# 1. /predict
r = requests.post(f"{BASE}/predict", headers=HEADERS,
                  json={"text": THREAT_TEXT, "persist": False})
d = r.json()
results["/predict"] = {
    "status": r.status_code,
    "primary_label": d.get("primary_label"),
    "evidence_plan_present": "evidence_plan" in d,
    "evidence_plan_keys": list(d.get("evidence_plan", {}).keys()) if d.get("evidence_plan") else None,
}

# 2. /predict/instant
r = requests.post(f"{BASE}/predict/instant", headers=HEADERS,
                  json={"text": THREAT_TEXT})
d = r.json()
results["/predict/instant"] = {
    "status": r.status_code,
    "primary_label": d.get("primary_label"),
    "evidence_plan_present": "evidence_plan" in d,
    "evidence_plan_keys": list(d.get("evidence_plan", {}).keys()) if d.get("evidence_plan") else None,
}

# 3. /predict/batch
r = requests.post(f"{BASE}/predict/batch", headers=HEADERS,
                  json={"texts": [THREAT_TEXT, "You are worthless, nobody wants you here."]})
d = r.json()
first = d.get("results", [{}])[0]
results["/predict/batch"] = {
    "status": r.status_code,
    "count": d.get("count"),
    "first_primary_label": first.get("primary_label"),
    "evidence_plan_present_in_first": "evidence_plan" in first,
    "evidence_plan_keys": list(first.get("evidence_plan", {}).keys()) if first.get("evidence_plan") else None,
}

# 4. /predict/conversation
r = requests.post(f"{BASE}/predict/conversation", headers=HEADERS,
                  json={"messages": [
                      {"sender": "alice", "text": THREAT_TEXT},
                      {"sender": "bob", "text": "Stop messaging me!"}
                  ]})
d = r.json()
results["/predict/conversation"] = {
    "status": r.status_code,
    "primary_label": d.get("primary_label"),
    "evidence_plan_present": "evidence_plan" in d,
    "evidence_plan_keys": list(d.get("evidence_plan", {}).keys()) if d.get("evidence_plan") else None,
}

# 5. /predict/audio — skip (requires audio file)
results["/predict/audio"] = {"status": "SKIPPED (requires multipart file upload)"}

# 6. /predict/screenshot — skip (requires image file)
results["/predict/screenshot"] = {"status": "SKIPPED (requires multipart image upload)"}

# 7. /predict/file — skip (requires file)
results["/predict/file"] = {"status": "SKIPPED (requires multipart file upload)"}

# 8. /predict/conversation/import — skip (requires file)
results["/predict/conversation/import"] = {"status": "SKIPPED (requires multipart txt/json upload)"}

with open("evidence_routes.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
