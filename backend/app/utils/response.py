"""
IntelliVault ~ Standardized API Response Helper
Ensures all REST endpoints return consistent JSON envelopes.
"""

from datetime import datetime, timezone
from flask import jsonify


def success_response(data=None, message="Operation successful", status_code=200, meta=None):
    """Formats a successful API response."""
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if meta:
        payload["meta"] = meta
    return jsonify(payload), status_code


def error_response(message="An unexpected error occurred", error_code="INTERNAL_ERROR", status_code=500, details=None):
    """Formats an error API response."""
    payload = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details if details is not None else {}
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return jsonify(payload), status_code
