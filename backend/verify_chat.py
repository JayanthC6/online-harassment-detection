import requests
import json

def verify_chat():
    evidence_plan = {
        "case_summary": "Extortion Risk Incident",
        "evidence_checklist": ["Screenshot of message", "Profile ID"],
        "why_flagged": "Detected 1 message involving extortion."
    }
    
    res = requests.post("http://127.0.0.1:5000/chat", json={
        "session_id": "test_session_1",
        "message": "What should I do? Someone is threatening me.",
        "persona": "user",
        "evidence_plan": evidence_plan
    })
    
    print("[CHATBOT RESPONSE]")
    print(res.json()["response"])

if __name__ == "__main__":
    verify_chat()
