from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from main import app
from auth import get_current_user
from db.model_notes import User, Base, File, Note
from db.init_db import get_db
from conftest import client

def test_health():
    response = client.get("/health")

    assert response.status_code == 200


def test_get_notes():
    response = client.get("/notes/")

    assert response.status_code == 200


def test_create_item():
    response = client.post(
        "/items/", json={"name": "Test Item", "description": "This is a test item"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert "id" in data


def test_read_item():
    # Create an item
    response = client.post(
        "/items/", json={"name": "Test Item", "description": "This is a test item"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    item_id = data["id"]

    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert data["id"] == item_id


def test_update_item():
    item_id = 1
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated Item", "description": "This is an updated item"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["description"] == "This is an updated item"
    assert data["id"] == item_id


def test_delete_item():
    item_id = 1
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == item_id
    # Try to get the deleted item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404, response.text


def setup() -> None:
    Base.metadata.create_all(bind=engine)


def teardown() -> None:
    Base.metadata.drop_all(bind=engine)

