import requests
import json

base_url = "http://localhost:5000"

try:
    r = requests.get(f"{base_url}/health")
    print("Health:", r.json())
    
    r = requests.post(f"{base_url}/admin/login", json={"username": "admin", "password": "password123"})
    token = r.json()["token"]
    print("Login:", "Success")
    
    r = requests.post(f"{base_url}/predict", json={"text": "You are a terrible person and I hate you!"})
    print("Predict:", r.json().get("label"))
    
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{base_url}/admin/stats", headers=headers)
    print("Admin Stats:", r.json().get("total_flagged"))

except Exception as e:
    print("Error:", str(e))
