"""
IntelliVault ~ Protected Current User (GET /api/auth/me) Tests
Verifies JWT authentication middleware, valid token decoding, token rejection
(missing, malformed, invalid, expired), and user profile payload sanitization.
"""

from datetime import datetime, timezone
import pytest
import mongomock
from backend.app import create_app
from backend.app.models.user import User
from backend.app.services.db import db_service
from backend.app.utils.security import hash_password, generate_access_token


@pytest.fixture
def me_client():
    """Provides a test client with an isolated in-memory database and seeded test users."""
    app = create_app(config_name="testing")
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["intellivault_test"]

    original_client = db_service.client
    original_db = db_service.db

    db_service.client = mock_client
    db_service.db = mock_db

    # Seed an active member user
    test_user = User(
        name="Diana Prince",
        email="diana@amazon.themyscira",
        password_hash=hash_password("Themyscira#2026!"),
        role="member",
        status="active"
    )
    mock_db["users"].insert_one(test_user.to_db_dict())

    # Seed a suspended user
    suspended_user = User(
        name="Ares War",
        email="ares@conflict.io",
        password_hash=hash_password("WarMonger#2026!"),
        role="member",
        status="suspended"
    )
    mock_db["users"].insert_one(suspended_user.to_db_dict())

    with app.test_client() as client:
        yield client, test_user, suspended_user, app

    db_service.client = original_client
    db_service.db = original_db


def test_get_me_with_valid_jwt(me_client):
    """
    Test 1: GET /api/auth/me with valid JWT returns HTTP 200.
    Test 5: password and password_hash are strictly omitted.
    Test 6: Correct user information is returned.
    """
    client, test_user, _, app = me_client
    secret_key = app.config["JWT_SECRET_KEY"]

    token = generate_access_token(
        user_id=str(test_user._id),
        email=test_user.email,
        role=test_user.role,
        secret_key=secret_key,
        expires_in_seconds=3600
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert "user" in data["data"]

    user_info = data["data"]["user"]
    assert user_info["id"] == str(test_user._id)
    assert user_info["name"] == "Diana Prince"
    assert user_info["email"] == "diana@amazon.themyscira"
    assert user_info["role"] == "member"
    assert user_info["status"] == "active"
    assert "created_at" in user_info

    # Security check: zero password leakage
    assert "password" not in user_info
    assert "password_hash" not in user_info


def test_get_me_without_token_fails(me_client):
    """Test 2: GET /api/auth/me without Authorization header returns HTTP 401."""
    client, _, _, _ = me_client

    response = client.get("/api/auth/me")
    assert response.status_code == 401

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_TOKEN"


@pytest.mark.parametrize("invalid_header", [
    "NotBearer token123",
    "Bearer",
    "Bearer token1 token2",
    "Token token123",
])
def test_get_me_with_malformed_header_fails(me_client, invalid_header):
    """Verifies that malformed Authorization header values return HTTP 401."""
    client, _, _, _ = me_client

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": invalid_header}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["code"] == "MALFORMED_TOKEN"


def test_get_me_with_invalid_signature_or_token(me_client):
    """Test 3: GET /api/auth/me with invalid/corrupted token returns HTTP 401."""
    client, test_user, _, _ = me_client

    # Sign with a bogus secret key
    fake_token = generate_access_token(
        user_id=str(test_user._id),
        email=test_user.email,
        role=test_user.role,
        secret_key="completely-wrong-secret-key-for-testing-purposes",
        expires_in_seconds=3600
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"}
    )
    assert response.status_code == 401

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_get_me_with_expired_token(me_client):
    """Test 4: GET /api/auth/me with expired token returns HTTP 401 TOKEN_EXPIRED."""
    client, test_user, _, app = me_client
    secret_key = app.config["JWT_SECRET_KEY"]

    # Generate token with negative lifetime (already expired)
    expired_token = generate_access_token(
        user_id=str(test_user._id),
        email=test_user.email,
        role=test_user.role,
        secret_key=secret_key,
        expires_in_seconds=-60
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_EXPIRED"


def test_get_me_with_suspended_account(me_client):
    """Verifies that a valid token belonging to a suspended account returns HTTP 403."""
    client, _, suspended_user, app = me_client
    secret_key = app.config["JWT_SECRET_KEY"]

    token = generate_access_token(
        user_id=str(suspended_user._id),
        email=suspended_user.email,
        role=suspended_user.role,
        secret_key=secret_key,
        expires_in_seconds=3600
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

    data = response.get_json()
    assert data["error"]["code"] == "ACCOUNT_DISABLED"
