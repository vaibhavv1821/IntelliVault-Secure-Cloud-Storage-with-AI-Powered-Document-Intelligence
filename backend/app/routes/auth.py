"""
IntelliVault ~ Authentication & Authorization API Routes
Handles user registration, identity verification, and credentials processing.
"""

from flask import Blueprint, request
from backend.app.services.auth_service import (
    register_user,
    ValidationError,
    DuplicateEmailError
)
from backend.app.utils.response import success_response, error_response
from backend.app.utils.logger import logger

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a new user account.
    Expects JSON payload: { "name": "...", "email": "...", "password": "..." }
    """
    if not request.is_json:
        return error_response(
            message="Content-Type must be application/json.",
            error_code="INVALID_CONTENT_TYPE",
            status_code=400
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response(
            message="Invalid or malformed JSON payload.",
            error_code="MALFORMED_PAYLOAD",
            status_code=400
        )

    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    try:
        user_data = register_user(name=name, email=email, password=password)
        return success_response(
            data={"user": user_data},
            message="User registered successfully.",
            status_code=201
        )
    except ValidationError as val_err:
        return error_response(
            message=str(val_err),
            error_code="VALIDATION_ERROR",
            status_code=400
        )
    except DuplicateEmailError as dup_err:
        return error_response(
            message=str(dup_err),
            error_code="EMAIL_ALREADY_EXISTS",
            status_code=409
        )
    except Exception as err:
        logger.error(f"Unexpected error during registration: {err}", exc_info=True)
        return error_response(
            message="An unexpected error occurred during user registration. Please try again later.",
            error_code="REGISTRATION_FAILED",
            status_code=500
        )
