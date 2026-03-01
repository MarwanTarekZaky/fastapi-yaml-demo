import httpx
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"].startswith("Hello")

def test_health():
    r = client.get("/health")
    assert r.status_code==200
    assert r.json()["status"] == "ok"

