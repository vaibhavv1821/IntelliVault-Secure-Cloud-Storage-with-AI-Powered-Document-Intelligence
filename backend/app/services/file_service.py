"""
IntelliVault ~ File Storage & Metadata Service
Orchestrates file validation, Supabase Storage binary upload, MongoDB metadata persistence,
and rollback mechanisms to eliminate orphaned storage objects.
"""

import os
import uuid
from bson import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from backend.app.models.file import FileMetadata, MAX_FILE_SIZE_BYTES
from backend.app.services.storage import storage_service
from backend.app.services.db import db_service
from backend.app.utils.logger import logger


class FileServiceError(Exception):
    """Base exception for file service operations."""
    pass


class FileValidationError(FileServiceError):
    """Raised when file validation constraints (presence, name, size) fail."""
    pass


class FileUploadError(FileServiceError):
    """Raised when storage upload or database persistence fails."""
    pass


class FileNotFoundServiceError(FileServiceError):
    """Raised when a requested file record does not exist in the database."""
    pass


class FileAccessDeniedError(FileServiceError):
    """Raised when a user attempts to access a file they do not own."""
    pass


class FileStorageDownloadError(FileServiceError):
    """Raised when retrieving a file binary stream from Supabase Storage fails."""
    pass


class FileStorageDeleteError(FileServiceError):
    """Raised when deleting a file from Supabase Storage or MongoDB fails."""
    pass


def ensure_file_indexes():
    """Creates indexes on the files collection for fast user queries and key uniqueness."""
    try:
        files_col = db_service.get_collection("files")
        files_col.create_index([("user_id", 1), ("created_at", -1)])
        files_col.create_index("storage_key", unique=True)
        logger.info("File collection indexes ensured successfully.")
    except Exception as e:
        logger.debug(f"File index creation deferred or already exists: {e}")


def upload_file(file_storage: FileStorage, user_id) -> dict:
    """
    Validates, uploads to Supabase Storage, and records metadata in MongoDB.
    Performs rollback on storage if database persistence fails.

    :param file_storage: Flask/Werkzeug FileStorage object.
    :param user_id: ObjectId or hex string of the authenticated user.
    :return: Serialized file metadata dictionary.
    """
    if file_storage is None or not hasattr(file_storage, "filename"):
        raise FileValidationError("No file provided in the upload request.")

    raw_filename = file_storage.filename
    if not raw_filename or not raw_filename.strip():
        raise FileValidationError("No file selected for upload.")

    original_name = raw_filename.strip()
    safe_name = secure_filename(original_name)
    if not safe_name:
        safe_name = "unnamed_file"

    # Read the entire file into memory (max 50 MB)
    file_storage.seek(0)
    file_data = file_storage.read()
    size_bytes = len(file_data)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({size_bytes} bytes) exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES} bytes (50 MB)."
        )

    # Format user_id
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    user_id_str = str(user_oid)

    # Generate unique collision-resistant storage path
    unique_id = uuid.uuid4().hex
    storage_key = f"user-files/{user_id_str}/{unique_id}_{safe_name}"

    content_type = getattr(file_storage, "content_type", None) or "application/octet-stream"

    if not storage_service._initialized:
        raise FileUploadError("Storage service is not initialized.")

    # 1. Upload binary data to Supabase Storage
    try:
        storage_service.upload(storage_key, file_data, content_type)
        logger.info(f"File uploaded to Supabase Storage: '{storage_key}' ({size_bytes} bytes)")
    except Exception as storage_err:
        logger.error(f"Supabase upload failed for '{storage_key}': {storage_err}", exc_info=True)
        raise FileUploadError(f"Failed to store file in object storage: {storage_err}")

    # 2. Persist metadata record in MongoDB
    file_record = FileMetadata(
        user_id=user_oid,
        original_name=original_name,
        storage_key=storage_key,
        content_type=content_type,
        size=size_bytes
    )

    try:
        files_col = db_service.get_collection("files")
        files_col.insert_one(file_record.to_db_dict())
        logger.info(f"File metadata saved in MongoDB for id: {file_record._id}")
    except Exception as db_err:
        logger.error(
            f"MongoDB metadata persistence failed for '{storage_key}': {db_err}. Initiating storage rollback...",
            exc_info=True
        )
        # Rollback: remove uploaded object to prevent orphan leaks
        try:
            storage_service.delete(storage_key)
            logger.info(f"Supabase Storage rollback completed for '{storage_key}'.")
        except Exception as rm_err:
            logger.warning(f"Failed to remove orphaned object '{storage_key}' during rollback: {rm_err}")
        raise FileUploadError(f"Failed to persist file record in database: {db_err}")

    return file_record.to_dict()


def get_user_files(user_id) -> list:
    """
    Retrieves all file metadata records owned by the specified user, sorted newest first.

    :param user_id: ObjectId or hex string of the user.
    :return: List of serialized file metadata dictionaries.
    """
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    files_col = db_service.get_collection("files")

    cursor = files_col.find({"user_id": user_oid}).sort("created_at", -1)
    results = []
    for doc in cursor:
        record = FileMetadata.from_db(doc)
        if record:
            results.append(record.to_dict())

    return results


def download_file(file_id: str, user_id) -> tuple:
    """
    Downloads file content from Supabase Storage after verifying user ownership.
    Returns the raw file bytes and metadata so the route can stream them to the client.

    :param file_id: Hex string or ObjectId of the target file.
    :param user_id: Hex string or ObjectId of the requesting user.
    :return: Tuple of (file_bytes: bytes, file_record: FileMetadata).
    """
    if not file_id or not isinstance(file_id, (str, ObjectId)):
        raise FileValidationError("File ID must be provided.")
    if isinstance(file_id, str) and not ObjectId.is_valid(file_id):
        raise FileValidationError("Invalid file ID format.")

    file_oid = ObjectId(file_id)
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id

    files_col = db_service.get_collection("files")
    doc = files_col.find_one({"_id": file_oid})
    if not doc:
        raise FileNotFoundServiceError(f"File with ID '{file_id}' not found.")

    if doc.get("user_id") != user_oid:
        raise FileAccessDeniedError("Access denied: You do not have permission to access this file.")

    file_record = FileMetadata.from_db(doc)

    if not storage_service._initialized:
        raise FileStorageDownloadError("Storage service is not initialized.")

    try:
        file_bytes = storage_service.download(file_record.storage_key)
        return file_bytes, file_record
    except Exception as e:
        logger.error(f"Failed to download '{file_record.storage_key}' from Supabase Storage: {e}", exc_info=True)
        raise FileStorageDownloadError(f"Failed to retrieve file from object storage: {e}")


def delete_file(file_id: str, user_id) -> str:
    """
    Deletes an object from Supabase Storage and its metadata from MongoDB.
    Enforces user ownership. Does not delete metadata if storage removal fails.

    :param file_id: Hex string or ObjectId of the target file.
    :param user_id: Hex string or ObjectId of the requesting user.
    :return: The deleted file_id string.
    """
    if not file_id or not isinstance(file_id, (str, ObjectId)):
        raise FileValidationError("File ID must be provided.")
    if isinstance(file_id, str) and not ObjectId.is_valid(file_id):
        raise FileValidationError("Invalid file ID format.")

    file_oid = ObjectId(file_id)
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id

    files_col = db_service.get_collection("files")
    doc = files_col.find_one({"_id": file_oid})
    if not doc:
        raise FileNotFoundServiceError(f"File with ID '{file_id}' not found.")

    if doc.get("user_id") != user_oid:
        raise FileAccessDeniedError("Access denied: You do not have permission to delete this file.")

    file_record = FileMetadata.from_db(doc)

    if not storage_service._initialized:
        raise FileStorageDeleteError("Storage service is not initialized.")

    # 1. Delete object from Supabase Storage first
    try:
        storage_service.delete(file_record.storage_key)
        logger.info(f"Object '{file_record.storage_key}' removed from Supabase Storage.")
    except Exception as e:
        logger.error(f"Failed to delete '{file_record.storage_key}' from Supabase Storage: {e}", exc_info=True)
        raise FileStorageDeleteError(f"Failed to delete file from object storage: {e}")

    # 2. Remove metadata from MongoDB
    try:
        delete_result = files_col.delete_one({"_id": file_oid, "user_id": user_oid})
        if delete_result.deleted_count == 0:
            raise FileStorageDeleteError("Failed to remove file metadata from database.")
        logger.info(f"File metadata for ID '{file_id}' removed from MongoDB.")
    except Exception as db_err:
        logger.error(f"Database error deleting file metadata for ID '{file_id}': {db_err}", exc_info=True)
        raise FileStorageDeleteError(f"Failed to remove file record from database: {db_err}")

    return str(file_id)
