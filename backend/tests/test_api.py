"""
Unit tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "Sentinel-1" in data["sensors"][0]

def test_summary():
    res = client.get("/api/summary")
    assert res.status_code == 200
    data = res.json()
    assert len(data["districts"]) == 5
    assert data["districts"][0]["name"] == "Благовещенск"

def test_pairs():
    res = client.get("/api/pairs")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 11

def test_inspector():
    # Inspect Blagoveshchensk coordinates
    res = client.get("/api/inspector", params={
        "pair_id": "flood_2021_06_amur__blagoveshchensk",
        "lat": 50.29,
        "lon": 127.54
    })
    assert res.status_code == 200
    data = res.json()
    assert "telemetry" in data
    assert "reasoning" in data
