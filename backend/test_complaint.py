import requests
import json
import uuid

def run_test():
    # 1. Register User A
    username_a = f"testuser_a_{uuid.uuid4().hex[:6]}"
    login_res_a = requests.post("http://localhost:5000/auth/register", json={"username": username_a, "password": "user123"})
    token_a = login_res_a.json().get("token")
    if not token_a:
        print("Registration A failed:", login_res_a.text)
        return
    
    # 2. Register User B
    username_b = f"testuser_b_{uuid.uuid4().hex[:6]}"
    login_res_b = requests.post("http://localhost:5000/auth/register", json={"username": username_b, "password": "user123"})
    token_b = login_res_b.json().get("token")
    
    # 3. User A submits text to instant analysis
    headers_a = {"Authorization": f"Bearer {token_a}"}
    payload = {"text": "I will ruin your life if you don't send me money right now."}
    
    print(f"User A running instant analysis: {payload['text']}")
    res_a = requests.post("http://localhost:5000/predict/instant", json=payload, headers=headers_a)
    
    # 4. Fetch User A's history
    print("\n--- FETCHING FROM /history/my for User A ---")
    my_res_a = requests.get("http://localhost:5000/history/my", headers=headers_a)
    
    complaints = my_res_a.json().get("complaints", [])
    if complaints:
        latest = complaints[0]
        entry_id = latest.get("_id")
        print(f"User A has entry ID: {entry_id}")
        
        # 5. User B attempts to delete User A's history entry
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print(f"\n--- User B attempting to delete User A's entry ({entry_id}) ---")
        del_res_b = requests.delete(f"http://localhost:5000/history/{entry_id}", headers=headers_b)
        
        print("User B Delete Response:", del_res_b.status_code, del_res_b.text)
        assert del_res_b.status_code == 403, f"Expected 403, got {del_res_b.status_code}"
        
        # 6. User A deletes their own entry
        print(f"\n--- User A attempting to delete their own entry ({entry_id}) ---")
        del_res_a = requests.delete(f"http://localhost:5000/history/{entry_id}", headers=headers_a)
        print("User A Delete Response:", del_res_a.status_code, del_res_a.text)
        assert del_res_a.status_code == 200, f"Expected 200, got {del_res_a.status_code}"
        
        print("\nAll tests passed successfully!")
    else:
        print("No complaints returned! Response:", my_res_a.text)

if __name__ == "__main__":
    run_test()
