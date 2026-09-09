import requests
import json

def verify():
    # 1. Test /predict
    res_predict = requests.post("http://127.0.0.1:5000/predict", headers={
        "Origin": "http://127.0.0.1:3000"
    }, json={
        "text": "I will find you and kill you.",
        "actor_id": "test_user",
        "persist": False
    })
    
    if "evidence_plan" in res_predict.json():
        print("[SUCCESS] /predict returned evidence_plan")
    else:
        print("[FAILED] /predict missing evidence_plan")
        print("Keys present:", list(res_predict.json().keys()))
        
    # 2. Test /predict/conversation/import
    whatsapp_text = "12/31/20, 10:00 AM - User: I hate you.\n12/31/20, 10:01 AM - User: You are dead."
    res_import = requests.post("http://127.0.0.1:5000/predict/conversation/import", files={
        "file": ("test.txt", whatsapp_text)
    })
    
    if "evidence_plan" in res_import.json():
        print("[SUCCESS] /predict/conversation/import returned evidence_plan")
    else:
        print("[FAILED] /predict/conversation/import missing evidence_plan")

if __name__ == "__main__":
    verify()
