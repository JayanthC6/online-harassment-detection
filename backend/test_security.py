import pytest
import json
import jwt
from datetime import datetime, timedelta
from app import app as flask_app
from core.database import db_instance
from core.config import Config

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    
    # Use fallback store for tests
    db_instance._db_enabled = False
    db_instance.fallback_store.clear()
    db_instance.fallback_conversations.clear()
    db_instance.fallback_profiles.clear()
    
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def generate_token(role="User", user="test_user"):
    payload = {
        "user": user,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def test_rbac_admin_endpoints(client):
    endpoints = [
        "/admin/stats",
        "/admin/reports",
        "/admin/analytics",
        "/admin/daily_counts",
        "/admin/conversations",
        "/admin/profiles"
    ]
    
    # Unauthenticated
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 401

    # Normal User
    user_token = generate_token(role="User")
    headers = {"Authorization": f"Bearer {user_token}"}
    for ep in endpoints:
        resp = client.get(ep, headers=headers)
        assert resp.status_code == 403
        
    # Admin
    admin_token = generate_token(role="Admin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    for ep in endpoints:
        resp = client.get(ep, headers=headers)
        assert resp.status_code == 200

def test_private_analysis_persist(client):
    user_token = generate_token(role="User", user="user1")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # persist=False
    resp = client.post("/predict/instant", json={"text": "I am angry", "persist": False}, headers=headers)
    assert resp.status_code == 200
    assert len(db_instance.fallback_store) == 0
    
    # persist=True
    resp = client.post("/predict/instant", json={"text": "I am angry", "persist": True}, headers=headers)
    assert resp.status_code == 200
    assert len(db_instance.fallback_store) == 1
    assert db_instance.fallback_store[0]["source"] == "self_serve"

def test_self_serve_isolation(client):
    user_token = generate_token(role="User", user="user1")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create self_serve record
    client.post("/predict/instant", json={"text": "I will kill you", "persist": True}, headers=headers)
    
    admin_token = generate_token(role="Admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    resp = client.get("/admin/reports", headers=admin_headers)
    data = json.loads(resp.data)
    assert len(data["reports"]) == 0
    
    resp = client.get("/admin/stats", headers=admin_headers)
    data = json.loads(resp.data)
    assert data["total_reports"] == 0
    
    resp = client.get("/admin/analytics", headers=admin_headers)
    data = json.loads(resp.data)
    assert data["risk_distribution"]["high"] == 0
    
    resp = client.get("/admin/profiles", headers=admin_headers)
    data = json.loads(resp.data)
    assert len(data["profiles"]) == 0

def test_data_ownership(client):
    user1_token = generate_token(role="User", user="user1")
    user2_token = generate_token(role="User", user="user2")
    
    h1 = {"Authorization": f"Bearer {user1_token}"}
    h2 = {"Authorization": f"Bearer {user2_token}"}
    
    # user1 creates record
    client.post("/predict/instant", json={"text": "test", "persist": True}, headers=h1)
    
    # user1 can see it
    r1 = client.get("/history/my", headers=h1)
    assert len(json.loads(r1.data)["complaints"]) == 1
    
    # user2 cannot see user1's record
    r2 = client.get("/history/my", headers=h2)
    assert len(json.loads(r2.data)["complaints"]) == 0
    
    # user2 tries to delete user1's record
    entry_id = json.loads(r1.data)["complaints"][0].get("_id", 0)
    r_del = client.delete(f"/history/{entry_id}", headers=h2)
    assert r_del.status_code == 403

def test_actor_profiling(client):
    user_token = generate_token(role="User", user="user1")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Analyze threatening text
    resp = client.post("/predict/instant", json={"text": "I will kill you", "persist": True}, headers=headers)
    data = json.loads(resp.data)
    assert data["primary_label"].lower() == "threat"
    
    # No profile created
    assert len(db_instance.fallback_profiles) == 0

def test_admin_reports_non_self_serve(client):
    admin_token = generate_token(role="Admin")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Inject a non_self_serve record (e.g. from chatbot/incident report)
    db_instance.fallback_store.append({
        "_id": 123,
        "source": "chatbot",
        "actor_id": "harasser_123",
        "user_id": "victim_456",
        "text_full": "I will kill you",
        "primary_label": "threat",
        "confidence": 0.9,
        "risk_score": 95,
        "logged_at": datetime.utcnow().isoformat()
    })
    
    # Admin sees it
    resp = client.get("/admin/reports", headers=headers)
    data = json.loads(resp.data)
    assert len(data["reports"]) == 1
    assert data["total"] == 1
