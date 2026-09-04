"""
IntelliVault ~ Password Hashing & Verification Unit Tests
Tests bcrypt hashing generation, salt uniqueness, constant-time verification,
and password policy validation.
"""

import pytest
from backend.app.utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    BCRYPT_MAX_BYTES
)


def test_hash_password_format():
    """Verifies that hash_password generates a valid modular bcrypt hash string."""
    plain = "SuperSecurePassword123!"
    hashed = hash_password(plain, rounds=10)

    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$10$")
    assert len(hashed) == 60


def test_hash_password_unique_salts():
    """Verifies that hashing the identical password twice produces distinct salt/ciphertext pairs."""
    plain = "SuperSecurePassword123!"
    hash1 = hash_password(plain, rounds=10)
    hash2 = hash_password(plain, rounds=10)

    assert hash1 != hash2
    assert verify_password(plain, hash1) is True
    assert verify_password(plain, hash2) is True


def test_verify_password_correct():
    """Verifies that verify_password returns True for the matching plaintext password."""
    plain = "P@ssw0rdSecureVault2026"
    hashed = hash_password(plain, rounds=10)

    assert verify_password(plain, hashed) is True


def test_verify_password_incorrect():
    """Verifies that verify_password returns False for an incorrect plaintext password."""
    plain = "P@ssw0rdSecureVault2026"
    hashed = hash_password(plain, rounds=10)

    assert verify_password("WrongP@ssw0rd2026", hashed) is False


@pytest.mark.parametrize("invalid_input", [
    ("", "$2b$10$validhashplaceholder"),
    (None, "$2b$10$validhashplaceholder"),
    ("validPassword123!", ""),
    ("validPassword123!", None),
    ("validPassword123!", "not_a_valid_bcrypt_hash"),
    ("validPassword123!", "$2b$invalid_rounds$invalidhash"),
])
def test_verify_password_invalid_inputs_safely_returns_false(invalid_input):
    """Verifies that malformed, empty, or None inputs safely return False without crashing."""
    pwd, hsh = invalid_input
    assert verify_password(pwd, hsh) is False


@pytest.mark.parametrize("empty_pwd", [
    "",
    None,
    12345,
])
def test_hash_password_empty_or_non_string_raises(empty_pwd):
    """Verifies that empty or invalid type inputs raise a ValueError."""
    with pytest.raises(ValueError, match="(?i)password"):
        hash_password(empty_pwd)


def test_hash_password_exceeding_72_bytes_raises():
    """
    Verifies that passwords exceeding 72 bytes are rejected with a clear error
    to prevent bcrypt's silent truncation security flaw.
    """
    long_password = "A" * 73
    with pytest.raises(ValueError, match="exceeds maximum length"):
        hash_password(long_password)


def test_validate_password_strength_success():
    """Verifies that a compliant password passes complexity validation."""
    valid_passwords = [
        "VaultPass#2026",
        "Str0ng&Secure!",
        "K3y$GCM@Encryption",
        "A" * 20 + "1a!Z"
    ]
    for pwd in valid_passwords:
        is_valid, error = validate_password_strength(pwd)
        assert is_valid is True
        assert error is None


@pytest.mark.parametrize("invalid_pwd, expected_error_fragment", [
    ("Short1!", "at least 8 characters"),
    ("nouppercase123!", "uppercase letter"),
    ("NOLOWERCASE123!", "lowercase letter"),
    ("NoDigitsHere!", "numerical digit"),
    ("NoSpecialChars123", "special character"),
    ("A" * 73 + "a1!", "cannot exceed 72 bytes"),
    (12345678, "must be a string"),
])
def test_validate_password_strength_failures(invalid_pwd, expected_error_fragment):
    """Verifies that non-compliant passwords fail with descriptive diagnostic messages."""
    is_valid, error = validate_password_strength(invalid_pwd)
    assert is_valid is False
    assert expected_error_fragment in error
