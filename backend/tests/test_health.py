"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health should return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    """GET /health should return {"status": "ok"}."""
    response = client.get("/health")
    data = response.json()
    assert data == {"status": "ok"}


def test_health_content_type_is_json():
    """GET /health should return application/json content type."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
