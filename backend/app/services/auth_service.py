"""
IntelliVault ~ Authentication Service
Implements core business logic for user account registration, credentials verification,
and unique account constraints.
"""

from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from backend.app.models.user import User
from backend.app.services.db import db_service
from backend.app.utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_access_token
)
from backend.app.utils.logger import logger


class RegistrationError(Exception):
    """Base exception for user registration failures."""
    pass


class ValidationError(RegistrationError):
    """Raised when user registration inputs fail validation rules."""
    pass


class DuplicateEmailError(RegistrationError):
    """Raised when an attempt is made to register with an existing email."""
    pass


class AuthenticationError(Exception):
    """Base exception for user authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials do not match or account does not exist."""
    pass


class AccountDisabledError(AuthenticationError):
    """Raised when an inactive, suspended, or pending user attempts to log in."""
    pass


def ensure_user_indexes():
    """
    Ensures that unique indexes are created for the users collection.
    Fails gracefully if the database is currently unreachable.
    """
    try:
        if db_service.db is not None:
            users_col = db_service.get_collection("users")
            users_col.create_index("email", unique=True)
            logger.info("Unique index on 'users.email' verified.")
    except Exception as e:
        logger.warning(f"Could not initialize user indexes: {e}")


def register_user(name: str, email: str, password: str) -> dict:
    """
    Registers a new user account:
    1. Validates presence and types of required inputs.
    2. Validates name constraints and email RFC format.
    3. Validates password complexity policy.
    4. Confirms email uniqueness.
    5. Hashes the password securely with bcrypt (12 rounds).
    6. Persists the user record to MongoDB.
    7. Returns the sanitized user profile (excluding password_hash).
    """
    # 1. Presence check
    if not name or not isinstance(name, str) or not name.strip():
        raise ValidationError("Name is required and must be a non-empty string.")

    if not email or not isinstance(email, str) or not email.strip():
        raise ValidationError("Email is required and must be a non-empty string.")

    if not password or not isinstance(password, str):
        raise ValidationError("Password is required and must be a non-empty string.")

    # 2. Schema normalization and validation via User domain model
    try:
        cleaned_name = User.validate_name(name)
        normalized_email = User.validate_and_normalize_email(email)
    except ValueError as val_err:
        raise ValidationError(str(val_err))

    # 3. Password policy check
    is_strong, password_err = validate_password_strength(password)
    if not is_strong:
        raise ValidationError(password_err)

    # 4. Database persistence and uniqueness check
    users_col = db_service.get_collection("users")

    # Application-level pre-check for clear diagnostics
    existing_user = users_col.find_one({"email": normalized_email})
    if existing_user:
        raise DuplicateEmailError("An account with this email address already exists.")

    # 5. Hash password (never log or store plaintext)
    password_hash = hash_password(password)

    # 6. Instantiate domain entity
    user = User(
        name=cleaned_name,
        email=normalized_email,
        password_hash=password_hash
    )

    # 7. Insert into MongoDB with DuplicateKeyError guard
    try:
        users_col.insert_one(user.to_db_dict())
        logger.info(f"User successfully registered: {user.email} (ID: {user._id})")
    except DuplicateKeyError:
        raise DuplicateEmailError("An account with this email address already exists.")
    except Exception as e:
        logger.error(f"Database error during user registration: {e}", exc_info=True)
        raise RuntimeError("Failed to persist user account due to a database error.")

    # 8. Return public serialized representation
    return user.to_dict(include_sensitive=False)


def authenticate_user(
    email: str,
    password: str,
    secret_key: str,
    expires_in_seconds: int = 86400
) -> dict:
    """
    Authenticates a user via email and password credentials:
    1. Validates presence and types of email and password.
    2. Normalizes email.
    3. Retrieves user record from MongoDB.
    4. Guards against user enumeration timing attacks via constant-time dummy verification.
    5. Verifies password using constant-time bcrypt verification.
    6. Verifies account status is 'active'.
    7. Updates last_login_at timestamp in MongoDB.
    8. Generates a signed JWT access token.
    9. Returns sanitized user dictionary and token metadata.
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise ValidationError("Email is required.")

    if not password or not isinstance(password, str):
        raise ValidationError("Password is required.")

    normalized_email = email.strip().lower()

    users_col = db_service.get_collection("users")
    user_doc = users_col.find_one({"email": normalized_email})

    if not user_doc:
        # Constant-time mitigation against user enumeration timing attacks
        verify_password(
            "dummy_mitigation_password",
            "$2b$12$e8YkY9u4q01234567890123456789012345678901234567890123"
        )
        raise InvalidCredentialsError("Invalid email or password.")

    user = User.from_db(user_doc)

    # Verify bcrypt password hash
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    # Check account status
    if user.status != "active":
        raise AccountDisabledError(
            f"Account is currently {user.status}. Please contact an administrator."
        )

    # Update last_login_at and updated_at in MongoDB
    now = datetime.now(timezone.utc)
    users_col.update_one(
        {"_id": user._id},
        {"$set": {"last_login_at": now, "updated_at": now}}
    )
    user.last_login_at = now
    user.updated_at = now

    # Generate JWT access token
    access_token = generate_access_token(
        user_id=str(user._id),
        email=user.email,
        role=user.role,
        secret_key=secret_key,
        expires_in_seconds=expires_in_seconds
    )

    logger.info(f"User successfully logged in: {user.email} (ID: {user._id})")

    return {
        "user": user.to_dict(include_sensitive=False),
        "token": {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in_seconds
        }
    }
