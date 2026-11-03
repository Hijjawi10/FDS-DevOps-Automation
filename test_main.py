import pytest
from fastapi.testclient import TestClient
from main import app, products

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_products():
    products.clear()
    products.update({
        1: {"name": "Laptop", "price": 800, "quantity": 10},
        2: {"name": "Keyboard", "price": 50, "quantity": 20}
    })


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "FDS DevOps Application is running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_products():
    response = client.get("/products")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_product():
    response = client.get("/products/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_product_not_found():
    response = client.get("/products/999")

    assert response.status_code == 404


def test_create_product():
    new_product = {
        "name": "Mouse",
        "price": 25,
        "quantity": 15
    }

    response = client.post("/products", json=new_product)

    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["product"]["name"] == "Mouse"


def test_update_product():
    updated_product = {
        "name": "Gaming Laptop",
        "price": 1200,
        "quantity": 5
    }

    response = client.put("/products/1", json=updated_product)

    assert response.status_code == 200
    assert response.json()["product"]["name"] == "Gaming Laptop"


def test_delete_product():
    response = client.delete("/products/2")

    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully"

    check = client.get("/products/2")
    assert check.status_code == 404
