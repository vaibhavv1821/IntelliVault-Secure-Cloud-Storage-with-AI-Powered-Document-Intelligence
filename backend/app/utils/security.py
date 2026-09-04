"""
IntelliVault ~ Security & Password Hashing Utilities
Provides production-grade bcrypt password hashing, constant-time verification,
and password policy validation.
"""

import re
import bcrypt

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
