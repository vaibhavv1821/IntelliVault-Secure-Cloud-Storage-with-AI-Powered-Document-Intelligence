"""
IntelliVault ~ Authentication & Authorization API Routes
Handles user registration, identity verification, and credentials processing.
"""

from flask import Blueprint, request, g
from backend.app.services.auth_service import (
    register_user,
    authenticate_user,
    ValidationError,
    DuplicateEmailError,
    InvalidCredentialsError,
    AccountDisabledError
)
from backend.app.utils.security import jwt_required
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


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates an existing user and returns a signed JWT access token.
    Expects JSON payload: { "email": "...", "password": "..." }
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

    email = payload.get("email")
    password = payload.get("password")

    from flask import current_app

    secret_key = current_app.config.get("JWT_SECRET_KEY")
    expires_hours = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24)
    expires_seconds = int(expires_hours * 3600)

    try:
        auth_data = authenticate_user(
            email=email,
            password=password,
            secret_key=secret_key,
            expires_in_seconds=expires_seconds
        )
        return success_response(
            data=auth_data,
            message="Login successful.",
            status_code=200
        )
    except ValidationError as val_err:
        return error_response(
            message=str(val_err),
            error_code="VALIDATION_ERROR",
            status_code=400
        )
    except InvalidCredentialsError as cred_err:
        return error_response(
            message=str(cred_err),
            error_code="INVALID_CREDENTIALS",
            status_code=401
        )
    except AccountDisabledError as dis_err:
        return error_response(
            message=str(dis_err),
            error_code="ACCOUNT_DISABLED",
            status_code=403
        )
    except Exception as err:
        logger.error(f"Unexpected error during login: {err}", exc_info=True)
        return error_response(
            message="An unexpected error occurred during login. Please try again later.",
            error_code="LOGIN_FAILED",
            status_code=500
        )


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user():
    """
    Returns the authenticated user's profile.
    Requires Authorization: Bearer <token>.
    """
    user = g.current_user
    return success_response(
        data={"user": user.to_dict(include_sensitive=False)},
        message="Current user profile retrieved successfully.",
        status_code=200
    )
