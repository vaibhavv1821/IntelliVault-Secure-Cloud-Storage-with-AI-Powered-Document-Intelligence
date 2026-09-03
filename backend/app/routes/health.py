"""
IntelliVault ~ Health & Diagnostics API Routes
Provides liveness and readiness endpoints for monitoring and frontend status checks.
"""

from datetime import datetime, timezone
import platform
import sys
from flask import Blueprint, current_app
from backend.app.services.db import db_service
from backend.app.services.storage import storage_service
from backend.app.utils.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def liveness():
    """Basic application liveness probe."""
    return success_response(
        data={
            "status": "healthy",
            "service": "IntelliVault API",
            "version": "0.1.0-alpha",
            "uptime_check": datetime.now(timezone.utc).isoformat()
        },
        message="IntelliVault API is active"
    )


@health_bp.route("/system/status", methods=["GET"])
def system_readiness():
    """Detailed readiness probe checking database, storage, and platform telemetry."""
    db_status = db_service.check_health()
    storage_status = storage_service.check_health()

    overall_healthy = db_status.get("connected", False) and storage_status.get("connected", False)

    return success_response(
        data={
            "status": "operational" if overall_healthy else "degraded",
            "environment": current_app.config.get("ENV", "development"),
            "services": {
                "database": db_status,
                "storage": storage_status
            },
            "platform": {
                "python_version": sys.version.split()[0],
                "os": platform.system(),
                "os_release": platform.release(),
                "machine": platform.machine()
            }
        },
        message="System readiness check completed",
        status_code=200
    )
