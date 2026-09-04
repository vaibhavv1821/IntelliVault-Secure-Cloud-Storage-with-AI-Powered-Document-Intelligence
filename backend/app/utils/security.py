"""
IntelliVault ~ Security & Password Hashing Utilities
Provides production-grade bcrypt password hashing, constant-time verification,
and password policy validation.
"""

import re
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

# Bcrypt workload factor (cost = 12 represents 4,096 hashing rounds)
DEFAULT_BCRYPT_ROUNDS = 12

# Maximum length accepted by bcrypt before silent truncation occurs
BCRYPT_MAX_BYTES = 72

# Minimum password length policy
MIN_PASSWORD_LENGTH = 8


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Validates password complexity against security policy:
    - Must be a non-empty string.
    - Minimum 8 characters.
    - Maximum 72 bytes (prevents silent bcrypt truncation).
    - Contains at least 1 uppercase letter.
    - Contains at least 1 lowercase letter.
    - Contains at least 1 digit.
    - Contains at least 1 special symbol.
    """
    if not isinstance(password, str):
        return False, "Password must be a string."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        return False, f"Password cannot exceed {BCRYPT_MAX_BYTES} bytes."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one numerical digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."

    return True, None


def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    """
    Hashes a plain-text password using bcrypt with a unique salt.
    Guarantees no silent truncation by enforcing maximum byte length.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password exceeds maximum length of {BCRYPT_MAX_BYTES} bytes. "
            "Truncation is disallowed to preserve cryptographic security."
        )

    salt = bcrypt.gensalt(rounds=rounds)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plain-text password against a bcrypt hash in constant time.
    Returns False safely if parameters are invalid or hash is malformed.
    """
    if not password or not isinstance(password, str):
        return False
    if not password_hash or not isinstance(password_hash, str):
        return False

    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError):
        # Gracefully handle malformed hash representations
        return False


# JWT Configuration Defaults
JWT_DEFAULT_ALGORITHM = "HS256"


def generate_access_token(
    user_id: str,
    email: str,
    role: str,
    secret_key: str,
    expires_in_seconds: int = 86400,
    algorithm: str = JWT_DEFAULT_ALGORITHM
) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Claims embedded:
    - sub: unique user identifier
    - email: user account email address
    - role: role-based access control level
    - iat: issued-at UTC timestamp
    - exp: expiration UTC timestamp
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string.")
    if not email or not isinstance(email, str):
        raise ValueError("email must be a non-empty string.")
    if not role or not isinstance(role, str):
        raise ValueError("role must be a non-empty string.")
    if not secret_key or not isinstance(secret_key, str):
        raise ValueError("secret_key must be a non-empty string.")

    now = datetime.now(timezone.utc)
    expiration = now + timedelta(seconds=expires_in_seconds)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp())
    }

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str = JWT_DEFAULT_ALGORITHM
) -> dict:
    """
    Decodes and verifies a JWT access token against the configured signing key.
    Raises jwt.ExpiredSignatureError if token lifetime has lapsed.
    Raises jwt.InvalidTokenError for invalid signatures or malformed tokens.
    """
    return jwt.decode(token, secret_key, algorithms=[algorithm])


def jwt_required(f):
    """
    Route decorator requiring a valid JWT bearer token in the Authorization header.
    Validates token signature, expiration, and extracts the user context onto flask.g.current_user.
    """
    from functools import wraps
    from flask import request, g, current_app
    from bson import ObjectId
    from backend.app.models.user import User
    from backend.app.services.db import db_service
    from backend.app.utils.response import error_response

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return error_response(
                message="Authorization header is required.",
                error_code="MISSING_TOKEN",
                status_code=401
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response(
                message="Authorization header must follow format: Bearer <token>",
                error_code="MALFORMED_TOKEN",
                status_code=401
            )

        token = parts[1]
        secret_key = current_app.config.get("JWT_SECRET_KEY")

        try:
            payload = decode_access_token(token, secret_key)
        except jwt.ExpiredSignatureError:
            return error_response(
                message="Authentication token has expired. Please log in again.",
                error_code="TOKEN_EXPIRED",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return error_response(
                message="Invalid authentication token.",
                error_code="INVALID_TOKEN",
                status_code=401
            )
        except Exception:
            return error_response(
                message="Failed to validate authentication token.",
                error_code="TOKEN_VALIDATION_FAILED",
                status_code=401
            )

        user_id = payload.get("sub")
        if not user_id:
            return error_response(
                message="Token payload is missing subject claim.",
                error_code="INVALID_TOKEN",
                status_code=401
            )

        users_col = db_service.get_collection("users")
        try:
            obj_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            user_doc = users_col.find_one({"_id": obj_id})
        except Exception:
            user_doc = None

        if not user_doc:
            return error_response(
                message="Authenticated user account does not exist.",
                error_code="USER_NOT_FOUND",
                status_code=401
            )

        user = User.from_db(user_doc)
        if user.status != "active":
            return error_response(
                message=f"Account is currently {user.status}.",
                error_code="ACCOUNT_DISABLED",
                status_code=403
            )

        g.current_user = user
        return f(*args, **kwargs)

    return decorated
