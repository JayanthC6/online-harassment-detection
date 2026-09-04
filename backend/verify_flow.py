import requests

# 1. Register a user
BASE_URL = "http://127.0.0.1:5000"
username = "testuser_verify"
password = "TestUser123!"

# try register
requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})

# login
res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
token = res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Call /predict with persist=False
print("Calling /predict...")
predict_res = requests.post(f"{BASE_URL}/predict", json={
    "text": "Everyone would be better off if you just disappeared. We know you don't belong here, and soon everyone else will too.",
    "persist": False
}, headers=headers)
data = predict_res.json()
print("Predict Result:")
print("Primary Label:", data.get("primary_label"))
print("Severity:", data.get("severity"))
print("Guidance:", data.get("guidance_snippet"))

# 3. Call /complaints to submit
print("\nCalling /complaints...")
complaint_res = requests.post(f"{BASE_URL}/complaints", json={
    "text": "Everyone would be better off if you just disappeared. We know you don't belong here, and soon everyone else will too."
}, headers=headers)
print("Complaint Result:", complaint_res.status_code)

# 4. Check My Tickets (User queue)
tickets_res = requests.get(f"{BASE_URL}/complaints", headers=headers)
print("My Tickets count:", len(tickets_res.json()))

