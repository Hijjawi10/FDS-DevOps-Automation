
import os

# Prevent connecting to PostgreSQL during tests
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models


# SQLite database in memory
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


# Override production database dependency
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
    assert created.status_code == 201

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
    assert created.status_code == 201

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
    assert created.status_code == 201

    product_id = created.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully"

    check = client.get(f"/products/{product_id}")
    assert check.status_code == 404




def test_register_user(client):
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/register", json=user)

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True

    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    first_user = {
        "username": "duplicateuser",
        "email": "first@example.com",
        "password": "SecurePassword123!"
    }

    second_user = {
        "username": "duplicateuser",
        "email": "second@example.com",
        "password": "SecurePassword123!"
    }

    first_response = client.post("/auth/register", json=first_user)
    assert first_response.status_code == 201

    response = client.post("/auth/register", json=second_user)

    assert response.status_code == 409


def test_register_duplicate_email(client):
    first_user = {
        "username": "firstuser",
        "email": "duplicate@example.com",
        "password": "SecurePassword123!"
    }

    second_user = {
        "username": "seconduser",
        "email": "duplicate@example.com",
        "password": "SecurePassword123!"
    }

    first_response = client.post("/auth/register", json=first_user)
    assert first_response.status_code == 201

    response = client.post("/auth/register", json=second_user)

    assert response.status_code == 409


def test_register_invalid_email(client):
    user = {
        "username": "invalidemail",
        "email": "not-an-email",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/register", json=user)

    assert response.status_code == 422


def test_register_weak_password(client):
    user = {
        "username": "weakpassword",
        "email": "weak@example.com",
        "password": "123"
    }

    response = client.post("/auth/register", json=user)

    assert response.status_code == 422


def test_password_is_hashed(client):
    from app.models import User
    from app.security import verify_password

    user = {
        "username": "hashuser",
        "email": "hash@example.com",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/register", json=user)

    assert response.status_code == 201

    db = TestingSessionLocal()

    try:
        saved_user = db.query(User).filter(
            User.username == "hashuser"
        ).first()

        assert saved_user is not None

        assert saved_user.hashed_password != user["password"]

        assert saved_user.hashed_password.startswith("$argon2id$")

        assert verify_password(
            user["password"],
            saved_user.hashed_password
        )

        assert saved_user.role == "user"

    finally:
        db.close()


def test_login_user(client, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-jwt-authentication-123456789"
    )

    user = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "SecurePassword123!"
    }

    register = client.post("/auth/register", json=user)
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "username": user["username"],
            "password": user["password"]
        }
    )

    assert login.status_code == 200

    data = login.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0



def test_get_current_user(client, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-jwt-authentication-123456789"
    )

    user = {
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "SecurePassword123!"
    }

    assert client.post("/auth/register", json=user).status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "username": user["username"],
            "password": user["password"]
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "profileuser"
    assert response.json()["email"] == "profile@example.com"
    assert response.json()["role"] == "user"
    assert "hashed_password" not in response.json()


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
