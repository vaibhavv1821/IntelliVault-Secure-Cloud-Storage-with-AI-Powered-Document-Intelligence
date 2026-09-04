"""
IntelliVault ~ Application Factory Module
Instantiates and configures the Flask application, extensions, services, and blueprints.
"""

import os
from flask import Flask
from flask_cors import CORS
from backend.app.config import config_by_name
from backend.app.services.db import db_service
from backend.app.services.storage import storage_service
from backend.app.routes.health import health_bp
from backend.app.routes.auth import auth_bp
from backend.app.routes.files import files_bp
from backend.app.services.auth_service import ensure_user_indexes
from backend.app.services.file_service import ensure_file_indexes
from backend.app.utils.logger import logger
from backend.app.utils.response import error_response


def create_app(config_name=None):
    """Application factory for IntelliVault."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_class)

    # Configure CORS - allow all origins in development, configurable in production
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize persistence and object storage singletons
    db_service.init_app(app)
    storage_service.init_app(app)

    # Ensure database indexes (skip blocking network check in testing mode)
    if not app.config.get("TESTING", False):
        ensure_user_indexes()
        ensure_file_indexes()

    # Register Blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(files_bp, url_prefix="/api/files")


    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response(
            message="The requested endpoint was not found.",
            error_code="NOT_FOUND",
            status_code=404
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response(
            message="HTTP method not allowed for this endpoint.",
            error_code="METHOD_NOT_ALLOWED",
            status_code=405
        )

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return error_response(
            message="An unexpected server error occurred. Please contact the administrator.",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500
        )

    logger.info(f"IntelliVault application initialized successfully in [{config_name}] mode.")
    return app
