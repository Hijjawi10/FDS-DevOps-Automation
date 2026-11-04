
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
import models
import os


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "FDS DevOps Application is running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_products(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []


def test_get_product(client):
    product = {
        "name": "Laptop",
        "price": 800,
        "quantity": 10
    }

    created = client.post("/products", json=product)
    product_id = created.json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_product_not_found(client):
    response = client.get("/products/999")

    assert response.status_code == 404


def test_create_product(client):
    product = {
        "name": "Mouse",
        "price": 25,
        "quantity": 15
    }

    response = client.post("/products", json=product)

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["product"]["name"] == "Mouse"


def test_update_product(client):
    product = {
        "name": "Laptop",
        "price": 800,
        "quantity": 10
    }

    created = client.post("/products", json=product)
    product_id = created.json()["id"]

    updated_product = {
        "name": "Gaming Laptop",
        "price": 1200,
        "quantity": 5
    }

    response = client.put(
        f"/products/{product_id}",
        json=updated_product
    )

    assert response.status_code == 200
    assert response.json()["product"]["name"] == "Gaming Laptop"


def test_delete_product(client):
    product = {
        "name": "Keyboard",
        "price": 50,
        "quantity": 20
    }

    created = client.post("/products", json=product)
    product_id = created.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully"

    check = client.get(f"/products/{product_id}")
    assert check.status_code == 404
