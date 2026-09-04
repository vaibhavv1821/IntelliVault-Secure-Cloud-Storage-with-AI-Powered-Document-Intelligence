"""
IntelliVault ~ Route Blueprints Package
"""

from backend.app.routes.health import health_bp
from backend.app.routes.auth import auth_bp

__all__ = ["health_bp", "auth_bp"]
