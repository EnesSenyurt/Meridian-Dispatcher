from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_delivery_returns_201():
    inserted_id = MagicMock()
    inserted_id.__str__ = lambda self: "64f0000000000000000000ab"

    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "insert_one":
            result = MagicMock()
            result.inserted_id = inserted_id
            return result

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/delivery",
            json={
                "sender_id": "uid1",
                "recipient_name": "John Doe",
                "recipient_address": "123 Main St",
                "recipient_phone": "555-0000",
                "package_description": "Electronics",
                "status": "pending"
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recipient_name"] == "John Doe"
    assert data["id"] == "64f0000000000000000000ab"
    assert "_links" in data
    assert data["_links"]["self"] == "/delivery/64f0000000000000000000ab"

def test_get_delivery_not_found_returns_404():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return None

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.get("/delivery/64f0000000000000000000ab")
    assert resp.status_code == 404

def test_list_deliveries_returns_200():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find":
            cursor = AsyncMock()
            cursor.to_list = AsyncMock(return_value=[
                {
                    "_id": "64f0000000000000000000ab",
                    "sender_id": "uid1",
                    "recipient_name": "Bob",
                    "recipient_address": "Addr",
                    "recipient_phone": "123",
                    "package_description": "Box",
                    "status": "pending",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z"
                }
            ])
            return cursor

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.get("/delivery")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "_links" in resp.json()[0]

def test_update_delivery_returns_200():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one_and_update":
            return {
                "_id": "64f0000000000000000000ab",
                "sender_id": "uid1",
                "recipient_name": "Bob",
                "recipient_address": "Addr",
                "recipient_phone": "123",
                "package_description": "Box",
                "status": "in_transit",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z"
            }

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.put(
            "/delivery/64f0000000000000000000ab",
            json={"status": "in_transit"}
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_transit"
    assert "_links" in resp.json()

def test_delete_delivery_returns_204():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "delete_one":
            result = MagicMock()
            result.deleted_count = 1
            return result

    with patch("app.repository.db.execute", side_effect=fake_execute):
        resp = client.delete("/delivery/64f0000000000000000000ab")
    assert resp.status_code == 204
