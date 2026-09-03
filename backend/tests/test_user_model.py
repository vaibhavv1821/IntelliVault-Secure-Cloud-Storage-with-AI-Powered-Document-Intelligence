"""
IntelliVault ~ User Model Unit Tests
Tests schema validation, email normalization, defaults, serialization, and security safeguards.
"""

from datetime import datetime, timezone
import pytest
from bson import ObjectId
from backend.app.models.user import (
    User,
    DEFAULT_ROLE,
    DEFAULT_STATUS,
    VALID_ROLES,
    VALID_STATUSES
)


def test_create_valid_user_with_defaults():
    """Verifies that a User can be created with valid inputs and receives safe defaults."""
    user = User(
        name="Alice Engineer",
        email="alice@intellivault.io",
        password_hash="$2b$12$e8YkY9u4q..."
    )

    assert user.name == "Alice Engineer"
    assert user.email == "alice@intellivault.io"
    assert user.password_hash == "$2b$12$e8YkY9u4q..."
    assert user.role == DEFAULT_ROLE
    assert user.role == "member"
    assert user.status == DEFAULT_STATUS
    assert user.status == "active"
    assert isinstance(user._id, ObjectId)
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    assert user.last_login_at is None


def test_email_normalization():
    """Verifies that email is stripped of surrounding whitespace and converted to lowercase."""
    user = User(
        name="Bob Builder",
        email="   BoB.Builder@Example.COM  ",
        password_hash="$2b$12$hash123"
    )
    assert user.email == "bob.builder@example.com"


@pytest.mark.parametrize("invalid_email", [
    "",
    "   ",
    "plainaddress",
    "@missingusername.com",
    "username@.com",
    "username@site",
])
def test_invalid_email_raises_value_error(invalid_email):
    """Verifies that malformed email addresses raise a ValueError."""
    with pytest.raises(ValueError, match="(?i)email"):
        User(
            name="Test User",
            email=invalid_email,
            password_hash="$2b$12$hash123"
        )


@pytest.mark.parametrize("invalid_name", [
    "",
    "   ",
    "A",  # Less than 2 chars
    "A" * 101,  # More than 100 chars
])
def test_invalid_name_raises_value_error(invalid_name):
    """Verifies that names outside the length constraint raise a ValueError."""
    with pytest.raises(ValueError, match="(?i)name"):
        User(
            name=invalid_name,
            email="valid@example.com",
            password_hash="$2b$12$hash123"
        )


def test_empty_password_hash_raises_value_error():
    """Verifies that empty or whitespace-only password hash raises a ValueError."""
    with pytest.raises(ValueError, match="Password hash"):
        User(
            name="Test User",
            email="valid@example.com",
            password_hash="   "
        )


def test_invalid_role_raises_value_error():
    """Verifies that unsupported roles raise a ValueError."""
    with pytest.raises(ValueError, match="Invalid role"):
        User(
            name="Admin User",
            email="admin@example.com",
            password_hash="$2b$12$hash123",
            role="super_superuser"
        )


def test_invalid_status_raises_value_error():
    """Verifies that unsupported account statuses raise a ValueError."""
    with pytest.raises(ValueError, match="Invalid status"):
        User(
            name="Test User",
            email="user@example.com",
            password_hash="$2b$12$hash123",
            status="banned"
        )


def test_to_db_dict_serialization():
    """Verifies that to_db_dict() produces the expected MongoDB document representation."""
    user = User(
        name="Charlie Admin",
        email="charlie@example.com",
        password_hash="$2b$12$hashedpwd",
        role="admin",
        status="active"
    )
    doc = user.to_db_dict()

    assert doc["_id"] == user._id
    assert doc["name"] == "Charlie Admin"
    assert doc["email"] == "charlie@example.com"
    assert doc["password_hash"] == "$2b$12$hashedpwd"
    assert doc["role"] == "admin"
    assert doc["status"] == "active"
    assert doc["created_at"] == user.created_at
    assert doc["updated_at"] == user.updated_at
    assert doc["last_login_at"] is None


def test_to_dict_omits_password_hash_by_default():
    """Verifies that the safe API dictionary never leaks the password_hash."""
    user = User(
        name="Diana Prince",
        email="diana@themyscira.io",
        password_hash="$2b$12$supersecrethash"
    )
    safe_dict = user.to_dict()

    assert "password_hash" not in safe_dict
    assert safe_dict["id"] == str(user._id)
    assert safe_dict["email"] == "diana@themyscira.io"
    assert safe_dict["role"] == "member"
    assert isinstance(safe_dict["created_at"], str)

    # When explicitly requested (e.g. for internal auth verification)
    internal_dict = user.to_dict(include_sensitive=True)
    assert "password_hash" in internal_dict


def test_from_db_reconstruction():
    """Verifies that from_db accurately reconstructs a User instance from a MongoDB document."""
    fixed_id = ObjectId()
    fixed_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
    raw_doc = {
        "_id": fixed_id,
        "name": "Eve Operator",
        "email": "eve@intellivault.io",
        "password_hash": "$2b$12$evehash",
        "role": "viewer",
        "status": "active",
        "created_at": fixed_time,
        "updated_at": fixed_time,
        "last_login_at": None
    }

    user = User.from_db(raw_doc)

    assert user._id == fixed_id
    assert user.name == "Eve Operator"
    assert user.email == "eve@intellivault.io"
    assert user.password_hash == "$2b$12$evehash"
    assert user.role == "viewer"
    assert user.status == "active"
    assert user.created_at == fixed_time
    assert user.updated_at == fixed_time
    assert user.last_login_at is None
