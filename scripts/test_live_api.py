import sys
import os
import time
import threading
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from app import app

def run_server():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def test_api():
    base_url = "http://127.0.0.1:5000"
    print(f"Waiting for server at {base_url}...")
    
    # Wait for server to come up
    for _ in range(30):
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.status_code == 200:
                print("Server is responding to /health!")
                break
        except Exception:
            time.sleep(1)
    else:
        print("FAIL: Server did not respond in 30s")
        sys.exit(1)

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

    print("\n--- 1. Health Checks ---")
    r1 = requests.get(f"{base_url}/health")
    check("GET /health", r1.status_code == 200, f"status={r1.status_code}")
    r2 = requests.get(f"{base_url}/api/health")
    check("GET /api/health", r2.status_code == 200, f"status={r2.status_code}")

    print("\n--- 2. Authentication ---")
    r_login = requests.post(f"{base_url}/admin/login", json={"username": "admin", "password": "password123"})
    check("POST /admin/login (dev pwd)", r_login.status_code == 200, f"status={r_login.status_code}")
    token = r_login.json().get("token")
    check("JWT token returned", bool(token), f"token_len={len(token) if token else 0}")
    
    r_login_api = requests.post(f"{base_url}/api/admin/login", json={"username": "admin", "password": "Sh13ldAI!Prod#2026"})
    check("POST /api/admin/login (prod pwd)", r_login_api.status_code == 200, f"status={r_login_api.status_code}")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- 3. Prediction / Analyze Endpoints ---")
    threat_text = "I will find you and hurt your family if you don't pay 1000 dollars."
    r_pred = requests.post(f"{base_url}/predict", json={"text": threat_text})
    check("POST /predict", r_pred.status_code == 200, f"label={r_pred.json().get('primary_label')}")
    
    r_ana = requests.post(f"{base_url}/api/analyze", json={"text": threat_text})
    check("POST /api/analyze", r_ana.status_code == 200, f"risk={r_ana.json().get('risk_score')}")

    r_inst = requests.post(f"{base_url}/predict/instant", json={"text": "You are amazing, thanks!"})
    check("POST /predict/instant (clean)", r_inst.status_code == 200, f"risk={r_inst.json().get('risk_score')}")

    print("\n--- 4. Batch Processing (Extension) ---")
    batch_payload = {"texts": ["Hello there", "I will kill you", "Win a free iPhone now"]}
    r_batch = requests.post(f"{base_url}/predict/batch", json=batch_payload)
    check("POST /predict/batch", r_batch.status_code == 200 and len(r_batch.json().get("results", [])) == 3)
    
    r_api_batch = requests.post(f"{base_url}/api/batch", json=batch_payload)
    check("POST /api/batch", r_api_batch.status_code == 200 and len(r_api_batch.json().get("results", [])) == 3)

    print("\n--- 5. Complaint Submission & History ---")
    r_comp = requests.post(f"{base_url}/complaints", json={"text": "Someone is stalking me online"}, headers=headers)
    check("POST /complaints", r_comp.status_code in (200, 201), f"status={r_comp.status_code}")
    
    r_comp_api = requests.post(f"{base_url}/api/complaints", json={"text": "Phishing email received"}, headers=headers)
    check("POST /api/complaints", r_comp_api.status_code in (200, 201), f"status={r_comp_api.status_code}")

    r_hist = requests.get(f"{base_url}/history/my", headers=headers)
    check("GET /history/my", r_hist.status_code == 200, f"count={len(r_hist.json().get('complaints', []))}")

    print("\n--- 6. Admin Endpoints ---")
    r_stats = requests.get(f"{base_url}/admin/stats", headers=headers)
    check("GET /admin/stats", r_stats.status_code == 200, f"total={r_stats.json().get('total_flagged')}")
    
    r_reports = requests.get(f"{base_url}/admin/reports", headers=headers)
    check("GET /admin/reports", r_reports.status_code == 200, f"total={r_reports.json().get('total')}")
    
    r_daily = requests.get(f"{base_url}/admin/daily_counts", headers=headers)
    check("GET /admin/daily_counts", r_daily.status_code == 200)

    print("\n--- 7. Security & Access Control ---")
    r_unauth = requests.get(f"{base_url}/admin/stats")
    check("GET /admin/stats without token returns 401", r_unauth.status_code == 401)
    
    r_bad_token = requests.get(f"{base_url}/admin/stats", headers={"Authorization": "Bearer badtoken"})
    check("GET /admin/stats with bad token returns 401", r_bad_token.status_code == 401)

    print(f"\n==========================================")
    print(f"Results: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print(f"==========================================")
    if passed == total:
        print("ALL END-TO-END FEATURES VERIFIED SUCCESSFULLY!")
        os._exit(0)
    else:
        print("SOME TESTS FAILED.")
        os._exit(1)

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    test_api()

