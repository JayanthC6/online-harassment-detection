"""
Pytest configuration and early DLL pre-initialization for ShieldAI test suite.
"""
import os
import sys
import pytest

# On Windows with Python 3.12, torch must load its runtime libraries (libiomp5md, c10)
# before numpy, scipy, or scikit-learn load conflicting OpenMP/MKL DLLs.
try:
    import torch
except Exception as _e:
    pass


@pytest.fixture(scope="module")
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "password123"})
    assert res.status_code == 200
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


