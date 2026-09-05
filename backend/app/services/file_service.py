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


class FileNotFoundServiceError(FileServiceError):
    """Raised when a requested file record does not exist in the database."""
    pass


class FileAccessDeniedError(FileServiceError):
    """Raised when a user attempts to access a file they do not own."""
    pass


class FileStorageDownloadError(FileServiceError):
    """Raised when retrieving a file binary stream from MinIO fails."""
    pass


class FileStorageDeleteError(FileServiceError):
    """Raised when deleting a file from MinIO or MongoDB fails."""
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


def download_file(file_id: str, user_id: ObjectId | str) -> tuple[bytes, FileMetadata]:
    """
    Retrieves and streams file content from MinIO after verifying user ownership.

    :param file_id: Hex string or ObjectId of the target file.
    :param user_id: Hex string or ObjectId of the requesting user.
    :return: Tuple of (file_bytes, FileMetadata).
    :raises FileValidationError: If file_id is invalid format.
    :raises FileNotFoundServiceError: If file record does not exist in database.
    :raises FileAccessDeniedError: If requesting user is not the file owner.
    :raises FileStorageDownloadError: If MinIO retrieval fails.
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
    bucket_name = storage_service.bucket_name or "intellivault-files"

    if not storage_service.client:
        raise FileStorageDownloadError("Object storage client is not initialized.")

    try:
        response = storage_service.client.get_object(bucket_name, file_record.storage_key)
        try:
            file_bytes = response.read()
        finally:
            if hasattr(response, "close"):
                response.close()
            if hasattr(response, "release_conn"):
                response.release_conn()
        return file_bytes, file_record
    except Exception as e:
        logger.error(f"Failed to retrieve object '{file_record.storage_key}' from MinIO: {e}", exc_info=True)
        raise FileStorageDownloadError(f"Failed to retrieve file from object storage: {e}")


def delete_file(file_id: str, user_id: ObjectId | str) -> str:
    """
    Deletes an object from MinIO and deletes its metadata from MongoDB.
    Enforces user ownership and atomic consistency (does not delete metadata if storage removal fails).

    :param file_id: Hex string or ObjectId of the target file.
    :param user_id: Hex string or ObjectId of the requesting user.
    :return: The deleted file_id string.
    :raises FileValidationError: If file_id is invalid format.
    :raises FileNotFoundServiceError: If file record does not exist in database.
    :raises FileAccessDeniedError: If requesting user is not the file owner.
    :raises FileStorageDeleteError: If MinIO deletion fails.
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
    bucket_name = storage_service.bucket_name or "intellivault-files"

    if not storage_service.client:
        raise FileStorageDeleteError("Object storage client is not initialized.")

    # 1. Delete object from MinIO first
    try:
        storage_service.client.remove_object(bucket_name, file_record.storage_key)
        logger.info(f"Object '{file_record.storage_key}' removed from MinIO bucket '{bucket_name}'.")
    except Exception as e:
        logger.error(f"Failed to delete object '{file_record.storage_key}' from MinIO: {e}", exc_info=True)
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

