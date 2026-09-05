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

from backend.app.services.file_service import (
    upload_file,
    download_file,
    delete_file,
    get_user_files,
    ensure_file_indexes,
    FileServiceError,
    FileValidationError,
    FileUploadError,
    FileNotFoundServiceError,
    FileAccessDeniedError,
    FileStorageDownloadError,
    FileStorageDeleteError
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
    "AccountDisabledError",
    "upload_file",
    "download_file",
    "delete_file",
    "get_user_files",
    "ensure_file_indexes",
    "FileServiceError",
    "FileValidationError",
    "FileUploadError",
    "FileNotFoundServiceError",
    "FileAccessDeniedError",
    "FileStorageDownloadError",
    "FileStorageDeleteError"
]


