from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "gemini_model" in body


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AI Coding Mentor Agent"
