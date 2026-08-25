import requests
import json
import time

def run_test():
    # 1. Register to get token
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    login_res = requests.post("http://localhost:5000/admin/register", json={"username": username, "password": "user123"})
    token = login_res.json().get("token")
    if not token:
        print("Registration failed:", login_res.text)
        return

    # 2. Submit extortion complaint
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"text": "I have your private photos and I will ruin your life if you don't send me $5000 in Bitcoin right now."}
    
    print(f"Submitting complaint: {payload['text']}")
    res = requests.post("http://localhost:5000/complaints", json=payload, headers=headers)
    
    # 3. Print the full response
    print("\n--- RAW API RESPONSE (HTTP", res.status_code, ") ---")
    print(json.dumps(res.json(), indent=2))
    
    # Also fetch the complaint to show the appended field
    print("\n--- FETCHING FROM /complaints/my ---")
    my_res = requests.get("http://localhost:5000/complaints/my", headers=headers)
    
    complaints = my_res.json().get("complaints", [])
    if complaints:
        latest = complaints[0]
        print(f"Severity: {latest.get('severity_tier')}")
        guidance = latest.get("user_guidance", "")
        with open("test_output.txt", "w", encoding="utf-8") as f:
            f.write(guidance)
        print("Guidance Block written to test_output.txt")
    else:
        print("No complaints returned! Response:", my_res.text)

if __name__ == "__main__":
    run_test()
