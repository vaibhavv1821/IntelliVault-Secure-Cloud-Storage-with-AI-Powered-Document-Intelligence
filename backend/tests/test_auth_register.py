"""
IntelliVault ~ User Registration Integration & Unit Tests
Verifies endpoint validation, duplicate constraints, password security,
database persistence, and standardized API response formats.
"""

import pytest
import mongomock
from backend.app import create_app
from backend.app.services.db import db_service
from backend.app.utils.security import verify_password


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

    # Initialize index on mock db
    mock_db["users"].create_index("email", unique=True)

    with app.test_client() as client:
        yield client, mock_db

    db_service.client = original_client
    db_service.db = original_db


def test_successful_registration(auth_client):
    """
    Test 1: Successful registration creates account, returns 201, and omits password_hash.
    Test 5: Password hash is not returned in the API response.
    """
    client, _ = auth_client
    payload = {
        "name": "Sarah Connor",
        "email": "sarah@resistance.org",
        "password": "Terminator#2026!"
    }

    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert "user" in data["data"]

    user_info = data["data"]["user"]
    assert user_info["name"] == "Sarah Connor"
    assert user_info["email"] == "sarah@resistance.org"
    assert "password_hash" not in user_info
    assert "password" not in user_info
    assert "id" in user_info


def test_user_stored_in_database(auth_client):
    """
    Test 2: User is actually stored in MongoDB collection.
    Test 3: Password is stored only as a hash.
    Test 4: Plaintext password is not stored anywhere in the database document.
    Test 12: Correct default role ('member').
    Test 13: Correct default account status ('active').
    """
    client, mock_db = auth_client
    raw_password = "SecurePassword@123"
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": raw_password
    }

    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    stored_user = mock_db["users"].find_one({"email": "john.doe@example.com"})
    assert stored_user is not None
    assert stored_user["name"] == "John Doe"
    assert stored_user["email"] == "john.doe@example.com"
    assert stored_user["role"] == "member"
    assert stored_user["status"] == "active"
    assert "created_at" in stored_user
    assert "updated_at" in stored_user

    # Verify password hash format and correctness
    assert "password_hash" in stored_user
    assert stored_user["password_hash"].startswith("$2b$12$")
    assert verify_password(raw_password, stored_user["password_hash"]) is True

    # Critical security check: Plaintext password must NOT exist in the document
    assert "password" not in stored_user
    assert stored_user.get("password_hash") != raw_password


def test_missing_name(auth_client):
    """Test 6: Missing name yields 400 Bad Request."""
    client, _ = auth_client
    response = client.post("/api/auth/register", json={
        "email": "noname@example.com",
        "password": "ValidPassword#123"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "name" in data["error"]["message"].lower()


def test_missing_email(auth_client):
    """Test 7: Missing email yields 400 Bad Request."""
    client, _ = auth_client
    response = client.post("/api/auth/register", json={
        "name": "No Email User",
        "password": "ValidPassword#123"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "email" in data["error"]["message"].lower()


def test_missing_password(auth_client):
    """Test 8: Missing password yields 400 Bad Request."""
    client, _ = auth_client
    response = client.post("/api/auth/register", json={
        "name": "No Password User",
        "email": "nopass@example.com"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in data["error"]["message"].lower()


@pytest.mark.parametrize("bad_email", [
    "plainaddress",
    "@missingusername.com",
    "user@.com",
    "user@site",
    "   ",
])
def test_invalid_email(auth_client, bad_email):
    """Test 9: Invalid email formats yield 400 Bad Request."""
    client, _ = auth_client
    response = client.post("/api/auth/register", json={
        "name": "Invalid Email User",
        "email": bad_email,
        "password": "ValidPassword#123"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("weak_password", [
    "short1!",        # Less than 8 chars
    "nouppercase123!", # Missing uppercase
    "NOLOWERCASE123!", # Missing lowercase
    "NoNumbersHere!",  # Missing digit
    "NoSpecial12345",  # Missing special char
    "A" * 73 + "a1!",  # Exceeds 72 bytes
])
def test_invalid_password(auth_client, weak_password):
    """Test 10: Passwords failing complexity policy yield 400 Bad Request."""
    client, _ = auth_client
    response = client.post("/api/auth/register", json={
        "name": "Weak Pass User",
        "email": "weakpass@example.com",
        "password": weak_password
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_email_conflict(auth_client):
    """
    Test 11: Registering with an already existing email returns 409 Conflict.
    Also tests that emails are normalized so case variations cannot bypass uniqueness.
    """
    client, _ = auth_client
    initial_payload = {
        "name": "Original User",
        "email": "unique.user@example.com",
        "password": "OriginalPassword#123"
    }
    first_response = client.post("/api/auth/register", json=initial_payload)
    assert first_response.status_code == 201

    # Attempt to register identical email with uppercase variation
    duplicate_payload = {
        "name": "Imposter User",
        "email": "UNIQUE.USER@example.com",
        "password": "DifferentPassword#456"
    }
    second_response = client.post("/api/auth/register", json=duplicate_payload)
    assert second_response.status_code == 409

    data = second_response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already exists" in data["error"]["message"].lower()


def test_invalid_content_type(auth_client):
    """Verifies that non-JSON requests are rejected with 400 Bad Request."""
    client, _ = auth_client
    response = client.post(
        "/api/auth/register",
        data="name=Test&email=test@example.com",
        content_type="application/x-www-form-urlencoded"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "INVALID_CONTENT_TYPE"
