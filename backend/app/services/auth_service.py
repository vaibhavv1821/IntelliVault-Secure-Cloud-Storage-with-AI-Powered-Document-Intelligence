"""
IntelliVault ~ Authentication Service
Implements core business logic for user account registration, credentials verification,
and unique account constraints.
"""

from pymongo.errors import DuplicateKeyError
from backend.app.models.user import User
from backend.app.services.db import db_service
from backend.app.utils.security import hash_password, validate_password_strength
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
