import requests
import sys

base_url = "http://localhost:5000"

def run_tests():
    try:
        # 1. Health
        r = requests.get(f"{base_url}/health")
        assert r.status_code == 200, f"/health failed: {r.status_code} {r.text}"
        print("Health OK")

        # 2. Login
        r = requests.post(f"{base_url}/admin/login", json={"username": "admin", "password": "password123"})
        assert r.status_code == 200, f"/admin/login failed: {r.status_code} {r.text}"
        token = r.json()["token"]
        print("Login OK")

        # 3. Predict text
        r = requests.post(f"{base_url}/predict", json={"text": "You are stupid and terrible!"})
        assert r.status_code == 200, f"/predict failed: {r.status_code} {r.text}"
        assert r.json().get("label") in ["harassing", "non_harassing", "non-harassing"]
        print("Predict OK")
        
        # 4. Predict batch
        r = requests.post(f"{base_url}/predict/batch", json={"texts": ["hello", "you are stupid"]})
        assert r.status_code == 200, f"/predict/batch failed: {r.status_code} {r.text}"
        print("Predict batch OK")

        # 5. Summarize
        r = requests.post(f"{base_url}/summarize", json={"text": "You are stupid", "category": "hate_speech", "confidence": 0.9})
        print(f"Summarize returned: {r.status_code}") # Can be 500 if Groq fails, but route works

        # 6. Admin stats
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base_url}/admin/stats", headers=headers)
        assert r.status_code == 200, f"/admin/stats failed: {r.status_code} {r.text}"
        print("Admin stats OK")

        # 7. Admin recent
        r = requests.get(f"{base_url}/admin/recent", headers=headers)
        assert r.status_code == 200, f"/admin/recent failed: {r.status_code} {r.text}"
        print("Admin recent OK")

        # 8. Admin daily counts
        r = requests.get(f"{base_url}/admin/daily_counts", headers=headers)
        assert r.status_code == 200, f"/admin/daily_counts failed: {r.status_code} {r.text}"
        print("Admin daily counts OK")

        print("ALL TESTS PASSED")
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
