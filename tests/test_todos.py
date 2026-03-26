import sys
from pathlib import Path

import pytest

# Add src/ to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlite3

from app import app
from repository import DATABASE, init_db


@pytest.fixture
def client():
    """Create a test client and reset the SQLite database before each test."""
    app.config["TESTING"] = True
    # Keep a connection alive so the shared in-memory DB persists across requests
    hold_conn = sqlite3.connect(DATABASE, uri=True)
    with app.app_context():
        init_db()
    with app.test_client() as client:
        yield client
    hold_conn.close()


class TestGetTodos:
    def test_empty_list(self, client):
        resp = client.get("/todos")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_returns_all(self, client):
        client.post("/todos", json={"title": "First"})
        client.post("/todos", json={"title": "Second"})
        resp = client.get("/todos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["title"] == "First"
        assert data[1]["title"] == "Second"


class TestGetTodoById:
    def test_get_existing(self, client):
        client.post("/todos", json={"title": "Test"})
        resp = client.get("/todos/1")
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Test"

    def test_get_not_found(self, client):
        resp = client.get("/todos/999")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


class TestCreateTodo:
    def test_create_with_title(self, client):
        resp = client.post("/todos", json={"title": "New todo"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "New todo"
        assert data["description"] == ""
        assert data["completed"] is False
        assert data["id"] == 1
        assert "created_at" in data

    def test_create_with_description(self, client):
        resp = client.post("/todos", json={"title": "Todo", "description": "Details"})
        assert resp.status_code == 201
        assert resp.get_json()["description"] == "Details"

    def test_create_missing_title(self, client):
        resp = client.post("/todos", json={})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_create_empty_title(self, client):
        resp = client.post("/todos", json={"title": ""})
        assert resp.status_code == 400

    def test_create_whitespace_title(self, client):
        resp = client.post("/todos", json={"title": "   "})
        assert resp.status_code == 400

    def test_create_title_too_long(self, client):
        resp = client.post("/todos", json={"title": "x" * 201})
        assert resp.status_code == 400
        assert "200" in resp.get_json()["error"]

    def test_create_title_at_limit(self, client):
        resp = client.post("/todos", json={"title": "x" * 200})
        assert resp.status_code == 201

    def test_create_strips_whitespace(self, client):
        resp = client.post("/todos", json={"title": "  Hello  "})
        assert resp.status_code == 201
        assert resp.get_json()["title"] == "Hello"

    def test_create_no_body(self, client):
        resp = client.post("/todos", content_type="application/json")
        assert resp.status_code == 400

    def test_auto_increment_ids(self, client):
        r1 = client.post("/todos", json={"title": "First"})
        r2 = client.post("/todos", json={"title": "Second"})
        assert r1.get_json()["id"] == 1
        assert r2.get_json()["id"] == 2


class TestUpdateTodo:
    def test_update_title(self, client):
        client.post("/todos", json={"title": "Original"})
        resp = client.put("/todos/1", json={"title": "Updated"})
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Updated"

    def test_update_completed(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.put("/todos/1", json={"completed": True})
        assert resp.status_code == 200
        assert resp.get_json()["completed"] is True

    def test_update_description(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.put("/todos/1", json={"description": "New desc"})
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "New desc"

    def test_update_multiple_fields(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.put("/todos/1", json={"title": "New", "completed": True})
        data = resp.get_json()
        assert data["title"] == "New"
        assert data["completed"] is True

    def test_update_not_found(self, client):
        resp = client.put("/todos/999", json={"title": "Nope"})
        assert resp.status_code == 404

    def test_update_no_body(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.put("/todos/1", content_type="application/json")
        assert resp.status_code == 400


class TestDeleteTodo:
    def test_delete_existing(self, client):
        client.post("/todos", json={"title": "To delete"})
        resp = client.delete("/todos/1")
        assert resp.status_code == 200
        assert "message" in resp.get_json()
        # Verify it's gone
        resp = client.get("/todos/1")
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/todos/999")
        assert resp.status_code == 404

    def test_delete_twice(self, client):
        client.post("/todos", json={"title": "To delete"})
        client.delete("/todos/1")
        resp = client.delete("/todos/1")
        assert resp.status_code == 404


class TestPatchTodo:
    """TDD: Tests written BEFORE the endpoint exists."""

    def test_patch_title_only(self, client):
        client.post("/todos", json={"title": "Original", "description": "Desc"})
        resp = client.patch("/todos/1", json={"title": "Patched"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["title"] == "Patched"
        assert data["description"] == "Desc"  # unchanged

    def test_patch_completed_only(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.patch("/todos/1", json={"completed": True})
        assert resp.status_code == 200
        assert resp.get_json()["completed"] is True
        assert resp.get_json()["title"] == "Task"  # unchanged

    def test_patch_not_found(self, client):
        resp = client.patch("/todos/999", json={"title": "Nope"})
        assert resp.status_code == 404

    def test_patch_no_body(self, client):
        client.post("/todos", json={"title": "Task"})
        resp = client.patch("/todos/1", content_type="application/json")
        assert resp.status_code == 400
