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
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string.")
    if not secret_key or not isinstance(secret_key, str):
        raise ValueError("secret_key must be a non-empty string.")

    return jwt.decode(token, secret_key, algorithms=[algorithm])
