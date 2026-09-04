"""
IntelliVault ~ User Login & JWT Generation Integration Tests
Verifies credentials verification, token generation, claim structures,
last_login telemetry tracking, and security error handling.
"""

from datetime import datetime, timezone, timedelta
import pytest
import mongomock
from backend.app import create_app
from backend.app.models.user import User
from backend.app.services.db import db_service
from backend.app.utils.security import hash_password, decode_access_token


@pytest.fixture
def auth_client():
    """Provides a configured Flask test client with an isolated in-memory MongoDB database."""
    app = create_app(config_name="testing")
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["intellivault_test"]

    original_client = db_service.client
    original_db = db_service.db

    db_service.client = mock_client
    db_service.db = mock_db

    # Seed an active test user
    test_password = "VaultPassword#2026"
    test_user = User(
        name="Bruce Wayne",
        email="bruce@wayne-enterprises.com",
        password_hash=hash_password(test_password),
        role="admin",
        status="active"
    )
    mock_db["users"].insert_one(test_user.to_db_dict())

    # Seed a suspended/disabled test user
    disabled_user = User(
        name="Oswald Cobblepot",
        email="oswald@iceberglounge.com",
        password_hash=hash_password("Penguin#2026!"),
        role="member",
        status="suspended"
    )
    mock_db["users"].insert_one(disabled_user.to_db_dict())

    with app.test_client() as client:
        yield client, mock_db, app

    db_service.client = original_client
    db_service.db = original_db


def test_successful_login_and_jwt_issuance(auth_client):
    """
    Test 1: Successful login returns HTTP 200.
    Test 2: Correct JWT access token returned.
    Test 3: JWT contains expected user identifier ('sub').
    Test 4: JWT expiration ('exp') is present and in the future.
    Test 5: Correct password succeeds.
    Test 14: password_hash is not returned.
    Test 15: password is never returned.
    """
    client, _, app = auth_client
    payload = {
        "email": "bruce@wayne-enterprises.com",
        "password": "VaultPassword#2026"
    }

    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert "token" in data["data"]
    assert "user" in data["data"]

    # Token structure verification
    token_info = data["data"]["token"]
    assert "access_token" in token_info
    assert token_info["token_type"] == "Bearer"
    assert token_info["expires_in"] == 86400

    # User profile payload verification
    user_info = data["data"]["user"]
    assert user_info["email"] == "bruce@wayne-enterprises.com"
    assert user_info["role"] == "admin"
    assert "password_hash" not in user_info
    assert "password" not in user_info

    # Verify JWT claims by decoding with test secret
    secret_key = app.config["JWT_SECRET_KEY"]
    decoded = decode_access_token(token_info["access_token"], secret_key)
    assert decoded["sub"] == user_info["id"]
    assert decoded["email"] == "bruce@wayne-enterprises.com"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
    assert "iat" in decoded
    assert decoded["exp"] > decoded["iat"]


def test_login_updates_last_login_timestamp(auth_client):
    """
    Test 12: last_login_at is populated/updated in MongoDB upon successful login.
    """
    client, mock_db, _ = auth_client

    # Verify initial last_login_at is None
    before_user = mock_db["users"].find_one({"email": "bruce@wayne-enterprises.com"})
    assert before_user["last_login_at"] is None

    response = client.post("/api/auth/login", json={
        "email": "bruce@wayne-enterprises.com",
        "password": "VaultPassword#2026"
    })
    assert response.status_code == 200

    after_user = mock_db["users"].find_one({"email": "bruce@wayne-enterprises.com"})
    assert after_user["last_login_at"] is not None
    assert isinstance(after_user["last_login_at"], datetime)


def test_incorrect_password_fails_and_does_not_update_last_login(auth_client):
    """
    Test 6: Incorrect password returns HTTP 401.
    Test 13: last_login_at is NOT updated after failed login.
    """
    client, mock_db, _ = auth_client

    response = client.post("/api/auth/login", json={
        "email": "bruce@wayne-enterprises.com",
        "password": "WrongPassword#999"
    })
    assert response.status_code == 401

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert "invalid email or password" in data["error"]["message"].lower()

    # Verify last_login_at remained None
    db_user = mock_db["users"].find_one({"email": "bruce@wayne-enterprises.com"})
    assert db_user["last_login_at"] is None


def test_nonexistent_account_fails_safely_with_generic_error(auth_client):
    """
    Test 7: Non-existent account fails safely with identical generic 401 error,
    preventing user enumeration timing attacks.
    """
    client, _, _ = auth_client

    response = client.post("/api/auth/login", json={
        "email": "ghost@doesnotexist.io",
        "password": "SomePassword#123"
    })
    assert response.status_code == 401

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert "invalid email or password" in data["error"]["message"].lower()


def test_missing_email_fails(auth_client):
    """Test 8: Missing email yields HTTP 400 Bad Request."""
    client, _, _ = auth_client
    response = client.post("/api/auth/login", json={
        "password": "VaultPassword#2026"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "email" in data["error"]["message"].lower()


def test_missing_password_fails(auth_client):
    """Test 9: Missing password yields HTTP 400 Bad Request."""
    client, _, _ = auth_client
    response = client.post("/api/auth/login", json={
        "email": "bruce@wayne-enterprises.com"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in data["error"]["message"].lower()


def test_invalid_content_type(auth_client):
    """Test 10: Non-JSON requests return HTTP 400 Bad Request."""
    client, _, _ = auth_client
    response = client.post(
        "/api/auth/login",
        data="email=test@example.com&password=abc",
        content_type="application/x-www-form-urlencoded"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "INVALID_CONTENT_TYPE"


def test_inactive_account_cannot_login(auth_client):
    """Test 11: Inactive or suspended accounts return HTTP 403 Forbidden."""
    client, _, _ = auth_client
    response = client.post("/api/auth/login", json={
        "email": "oswald@iceberglounge.com",
        "password": "Penguin#2026!"
    })
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"]["code"] == "ACCOUNT_DISABLED"
    assert "suspended" in data["error"]["message"].lower()


def test_email_normalization_on_login(auth_client):
    """Verifies that email casing and surrounding spaces are normalized on login."""
    client, _, _ = auth_client
    response = client.post("/api/auth/login", json={
        "email": "   BRUCE@wayne-enterprises.COM  ",
        "password": "VaultPassword#2026"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "bruce@wayne-enterprises.com"
