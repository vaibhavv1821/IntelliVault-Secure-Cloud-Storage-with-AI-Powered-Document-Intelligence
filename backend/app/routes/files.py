"""
IntelliVault ~ File Management API Routes
Provides endpoints for secure file upload and file metadata querying.
"""

from flask import Blueprint, request, g
from backend.app.services.file_service import (
    upload_file,
    get_user_files,
    FileValidationError,
    FileUploadError
)
from backend.app.utils.security import jwt_required
from backend.app.utils.response import success_response, error_response
from backend.app.utils.logger import logger

files_bp = Blueprint("files", __name__)


@files_bp.route("/upload", methods=["POST"])
@jwt_required
def handle_file_upload():
    """
    Handles file upload via multipart/form-data.
    Expects form field named 'file'.
    Returns metadata of the successfully uploaded file with HTTP 201.
    """
    if "file" not in request.files:
        return error_response(
            message="No file part in the multipart request.",
            error_code="NO_FILE_PART",
            status_code=400
        )

    uploaded_file = request.files["file"]

    if not uploaded_file.filename or not uploaded_file.filename.strip():
        return error_response(
            message="No file selected for upload.",
            error_code="NO_FILE_SELECTED",
            status_code=400
        )

    try:
        user = g.current_user
        file_metadata = upload_file(file_storage=uploaded_file, user_id=user._id)
        return success_response(
            data={"file": file_metadata},
            message="File uploaded successfully.",
            status_code=201
        )
    except FileValidationError as val_err:
        return error_response(
            message=str(val_err),
            error_code="FILE_VALIDATION_ERROR",
            status_code=400
        )
    except FileUploadError as upload_err:
        logger.error(f"File upload error: {upload_err}", exc_info=True)
        return error_response(
            message=str(upload_err),
            error_code="STORAGE_ERROR",
            status_code=500
        )
    except Exception as err:
        logger.error(f"Unexpected error during file upload: {err}", exc_info=True)
        return error_response(
            message="An unexpected error occurred during file upload. Please try again later.",
            error_code="UPLOAD_FAILED",
            status_code=500
        )


@files_bp.route("", methods=["GET"])
@jwt_required
def list_files():
    """
    Returns the list of uploaded files belonging to the authenticated user.
    """
    try:
        user = g.current_user
        files = get_user_files(user_id=user._id)
        return success_response(
            data={"files": files},
            message="User files retrieved successfully.",
            status_code=200
        )
    except Exception as err:
        logger.error(f"Unexpected error retrieving files for user: {err}", exc_info=True)
        return error_response(
            message="An unexpected error occurred while retrieving user files.",
            error_code="FILES_RETRIEVAL_FAILED",
            status_code=500
        )
