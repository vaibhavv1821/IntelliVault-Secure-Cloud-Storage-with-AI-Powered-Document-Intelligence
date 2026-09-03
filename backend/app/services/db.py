"""
IntelliVault ~ MongoDB Database Service
Provides singleton client management, collection access, and health diagnostics.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.app.utils.logger import logger


class MongoDBService:
    """Manages MongoDB connection lifecycle and collection handles."""

    def __init__(self):
        self.client = None
        self.db = None
        self.uri = None
        self.db_name = None

    def init_app(self, app):
        """Initializes the database client using Flask application configuration."""
        self.uri = app.config.get("MONGODB_URI")
        self.db_name = app.config.get("MONGODB_DB_NAME", "intellivault")
        timeout_ms = app.config.get("MONGODB_CONNECT_TIMEOUT_MS", 2000)

        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms
            )
            self.db = self.client[self.db_name]
            logger.info(f"MongoDB client initialized for database: '{self.db_name}'")
        except Exception as e:
            logger.warning(f"Failed to initialize MongoDB client: {e}")
            self.client = None
            self.db = None

    def check_health(self):
        """Pings the database and returns connection status details."""
        if not self.client:
            return {
                "connected": False,
                "type": "MongoDB",
                "database": self.db_name,
                "error": "Client not initialized"
            }

        try:
            # The ping command is cheap and does not require auth
            self.client.admin.command("ping")
            return {
                "connected": True,
                "type": "MongoDB",
                "database": self.db_name,
                "server_info": "Connected successfully"
            }
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.debug(f"MongoDB connection check failed: {e}")
            return {
                "connected": False,
                "type": "MongoDB",
                "database": self.db_name,
                "error": "Connection timed out or server unavailable",
                "hint": "Ensure local MongoDB service is running (mongod) or configure MONGODB_URI with a valid Atlas cluster string."
            }
        except Exception as e:
            logger.warning(f"Unexpected MongoDB error: {e}")
            return {
                "connected": False,
                "type": "MongoDB",
                "database": self.db_name,
                "error": str(e)
            }

    def get_collection(self, name):
        """Returns handle to a named collection."""
        if self.db is None:
            raise RuntimeError("Database service is not initialized.")
        return self.db[name]


# Global database service instance
db_service = MongoDBService()
