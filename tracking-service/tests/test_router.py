from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_update_location_returns_200():
    async def fake_execute(command, *args, **kwargs):
        if command == "set":
            return "OK"

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/tracking/123/location",
            json={"lat": 40.7, "lng": 29.9, "status": "on_way"}
        )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Location updated successfully"
    assert "_links" in resp.json()
    assert resp.json()["_links"]["delivery"] == "/delivery/123"

def test_get_location_returns_200():
    async def fake_execute(command, *args, **kwargs):
        if command == "get":
            return '{"lat": 40.7, "lng": 29.9, "status": "on_way"}'

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.get("/tracking/123/location")
    assert resp.status_code == 200
    assert resp.json()["lat"] == 40.7
    assert "_links" in resp.json()
    assert resp.json()["_links"]["self"] == "/tracking/123/location"

def test_get_location_not_found_returns_404():
    async def fake_execute(command, *args, **kwargs):
        if command == "get":
            return None

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.get("/tracking/999/location")
    assert resp.status_code == 404
