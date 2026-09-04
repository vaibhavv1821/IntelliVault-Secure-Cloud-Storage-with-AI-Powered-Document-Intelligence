"""
IntelliVault ~ Core Services Package
"""

from backend.app.services.db import db_service
from backend.app.services.storage import storage_service
from backend.app.services.auth_service import (
    register_user,
    authenticate_user,
    ensure_user_indexes,
    RegistrationError,
    ValidationError,
    DuplicateEmailError,
    AuthenticationError,
    InvalidCredentialsError,
    AccountDisabledError
)

__all__ = [
    "db_service",
    "storage_service",
    "register_user",
    "authenticate_user",
    "ensure_user_indexes",
    "RegistrationError",
    "ValidationError",
    "DuplicateEmailError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "AccountDisabledError"
]
