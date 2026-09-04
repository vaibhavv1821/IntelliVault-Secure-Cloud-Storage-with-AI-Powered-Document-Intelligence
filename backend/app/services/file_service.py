"""
IntelliVault ~ File Storage & Metadata Service
Orchestrates file validation, MinIO binary stream storage, MongoDB metadata persistence,
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


def ensure_file_indexes():
    """Creates indexes on the files collection for fast user queries and key uniqueness."""
    try:
        files_col = db_service.get_collection("files")
        files_col.create_index([("user_id", 1), ("created_at", -1)])
        files_col.create_index("storage_key", unique=True)
        logger.info("File collection indexes ensured successfully.")
    except Exception as e:
        logger.debug(f"File index creation deferred or already exists: {e}")


def upload_file(file_storage: FileStorage, user_id: ObjectId | str) -> dict:
    """
    Validates, streams to MinIO, and records metadata in MongoDB for an uploaded file.
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

    # Compute stream size by seeking to end and restoring pointer
    file_storage.seek(0, os.SEEK_END)
    size_bytes = file_storage.tell()
    file_storage.seek(0)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({size_bytes} bytes) exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES} bytes (50 MB)."
        )

    # Format user_id
    user_oid = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
    user_id_str = str(user_oid)

    # Generate unique collision-resistant storage key
    unique_id = uuid.uuid4().hex
    storage_key = f"user-files/{user_id_str}/{unique_id}_{safe_name}"

    content_type = getattr(file_storage, "content_type", None) or "application/octet-stream"
    bucket_name = storage_service.bucket_name or "intellivault-files"

    if not storage_service.client:
        raise FileUploadError("Storage service client is not initialized.")

    # 1. Upload binary stream to MinIO
    try:
        stream = getattr(file_storage, "stream", file_storage)
        storage_service.client.put_object(
            bucket_name=bucket_name,
            object_name=storage_key,
            data=stream,
            length=size_bytes,
            content_type=content_type
        )
        logger.info(f"File uploaded to MinIO: '{storage_key}' ({size_bytes} bytes)")
    except Exception as storage_err:
        logger.error(f"MinIO upload failed for '{storage_key}': {storage_err}", exc_info=True)
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
            f"MongoDB metadata persistence failed for '{storage_key}': {db_err}. Initiating MinIO rollback...",
            exc_info=True
        )
        # Rollback storage object to prevent orphan leaks
        try:
            storage_service.client.remove_object(bucket_name, storage_key)
            logger.info(f"MinIO rollback completed successfully for '{storage_key}'.")
        except Exception as rm_err:
            logger.warning(f"Failed to remove orphaned object '{storage_key}' during rollback: {rm_err}")
        raise FileUploadError(f"Failed to persist file record in database: {db_err}")

    return file_record.to_dict()


def get_user_files(user_id: ObjectId | str) -> list[dict]:
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
