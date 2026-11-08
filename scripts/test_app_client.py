import sys
import os
import json
import io

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from app import app

def run_tests():
    client = app.test_client()
    passed = 0
    total = 0

    def check(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {details}")
        else:
            print(f"  [FAIL] {name} {details}")

    print("\n--- 1. Health Checks (Root & /api) ---")
    r1 = client.get("/health")
    check("GET /health", r1.status_code == 200, f"status={r1.status_code}")
    r2 = client.get("/api/health")
    check("GET /api/health", r2.status_code == 200, f"status={r2.status_code}")

    print("\n--- 2. Authentication & JWT ---")
    r_login_dev = client.post("/admin/login", json={"username": "admin", "password": "password123"})
    check("POST /admin/login (dev pwd)", r_login_dev.status_code == 200, f"status={r_login_dev.status_code}")
    token = r_login_dev.json.get("token")
    check("JWT token returned", bool(token), f"token_len={len(token) if token else 0}")

    r_login_prod = client.post("/api/admin/login", json={"username": "admin", "password": "Sh13ldAI!Prod#2026"})
    check("POST /api/admin/login (prod pwd)", r_login_prod.status_code == 200, f"status={r_login_prod.status_code}")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- 3. Prediction / Analyze Endpoints ---")
    threat_text = "I know where you live. If you don't send me $5000 in Bitcoin by tomorrow, I will ruin your life and hurt your family."
    r_pred = client.post("/predict", json={"text": threat_text})
    check("POST /predict", r_pred.status_code == 200, f"label={r_pred.json.get('primary_label')}")
    
    r_ana = client.post("/api/analyze", json={"text": threat_text})
    check("POST /api/analyze", r_ana.status_code == 200, f"risk={r_ana.json.get('risk_score')}")

    r_inst = client.post("/predict/instant", json={"text": "Hey, are we still meeting for lunch tomorrow at 12? Let me know!"})
    check("POST /predict/instant (clean)", r_inst.status_code == 200, f"risk={r_inst.json.get('risk_score')}")

    r_demo = client.post("/demo/analyze", json={"example_id": "threat_example"})
    check("POST /demo/analyze", r_demo.status_code == 200, f"label={r_demo.json.get('primary_label')}")

    print("\n--- 4. Batch Processing (Extension) ---")
    batch_payload = {"texts": ["Hello there, nice to meet you", "I will kill you and your family", "Claim your free prize now http://scam.cc"]}
    r_batch = client.post("/predict/batch", json=batch_payload)
    check("POST /predict/batch", r_batch.status_code == 200 and len(r_batch.json.get("results", [])) == 3)

    r_api_batch = client.post("/api/batch", json=batch_payload)
    check("POST /api/batch", r_api_batch.status_code == 200 and len(r_api_batch.json.get("results", [])) == 3)

    print("\n--- 5. Complaints Submission & History ---")
    r_comp = client.post("/complaints", json={"text": "Someone is threatening to leak private photos unless I pay them."}, headers=headers)
    check("POST /complaints", r_comp.status_code in (200, 201), f"status={r_comp.status_code}")

    r_comp_api = client.post("/api/complaints", json={"text": "Urgent KYC update required or account will be suspended."}, headers=headers)
    check("POST /api/complaints", r_comp_api.status_code in (200, 201), f"status={r_comp_api.status_code}")

    r_hist = client.get("/history/my", headers=headers)
    check("GET /history/my", r_hist.status_code == 200, f"count={len(r_hist.json.get('complaints', []))}")

    r_hist_api = client.get("/api/history/my", headers=headers)
    check("GET /api/history/my", r_hist_api.status_code == 200)

    print("\n--- 6. Admin Endpoints ---")
    r_stats = client.get("/admin/stats", headers=headers)
    check("GET /admin/stats", r_stats.status_code == 200, f"total={r_stats.json.get('total_flagged')}")

    r_stats_api = client.get("/api/admin/stats", headers=headers)
    check("GET /api/admin/stats", r_stats_api.status_code == 200)

    r_reports = client.get("/admin/reports", headers=headers)
    check("GET /admin/reports", r_reports.status_code == 200, f"total={r_reports.json.get('total')}")

    r_daily = client.get("/admin/daily_counts", headers=headers)
    check("GET /admin/daily_counts", r_daily.status_code == 200)

    r_profiles = client.get("/admin/profiles", headers=headers)
    check("GET /admin/profiles", r_profiles.status_code == 200)

    print("\n--- 7. Security & Access Control ---")
    r_unauth = client.get("/admin/stats")
    check("GET /admin/stats without token returns 401", r_unauth.status_code == 401)

    r_bad_token = client.get("/admin/stats", headers={"Authorization": "Bearer invalid_token_xyz"})
    check("GET /admin/stats with invalid token returns 401", r_bad_token.status_code == 401)

    print("\n--- 8. File Upload & Chat Export ---")
    chat_export = """12/31/22, 10:45 AM - Alice: Hey how are you?
12/31/22, 10:46 AM - Bob: I will destroy you if you tell anyone!
12/31/22, 10:47 AM - Alice: Please leave me alone."""
    
    chat_file = (io.BytesIO(chat_export.encode("utf-8")), "chat.txt")
    r_chat_import = client.post("/predict/conversation/import", data={"file": chat_file}, content_type="multipart/form-data")
    check("POST /predict/conversation/import (WhatsApp TXT)", r_chat_import.status_code == 200, f"status={r_chat_import.status_code}")

    # Plain text document file upload
    doc_file = (io.BytesIO(b"Job Offer: Pay $500 processing fee to receive your appointment letter."), "offer.txt")
    r_file = client.post("/predict/file", data={"file": doc_file}, content_type="multipart/form-data")
    check("POST /predict/file (TXT)", r_file.status_code == 200, f"status={r_file.status_code}")

    r_file_api = client.post("/api/analyze/file", data={"file": (io.BytesIO(b"Normal message text"), "normal.txt")}, content_type="multipart/form-data")
    check("POST /api/analyze/file", r_file_api.status_code == 200, f"status={r_file_api.status_code}")

    print(f"\n==========================================")
    print(f"Results: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print(f"==========================================")
    if passed == total:
        print("ALL END-TO-END FEATURES VERIFIED SUCCESSFULLY!")
        return 0
    else:
        print("SOME TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())

