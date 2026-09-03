"""
IntelliVault ~ MinIO / S3 Object Storage Service
Provides client singleton, bucket initialization, and storage health diagnostics.
"""

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError
from backend.app.utils.logger import logger


class ObjectStorageService:
    """Manages connection to MinIO / S3-compatible object storage."""

    def __init__(self):
        self.client = None
        self.endpoint = None
        self.bucket_name = None
        self.secure = False

    def init_app(self, app):
        """Initializes the MinIO client using Flask application configuration."""
        self.endpoint = app.config.get("MINIO_ENDPOINT", "127.0.0.1:9000")
        self.access_key = app.config.get("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = app.config.get("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = app.config.get("MINIO_BUCKET_NAME", "intellivault-files")
        self.secure = app.config.get("MINIO_SECURE", False)

        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            logger.info(f"MinIO storage client initialized for endpoint: '{self.endpoint}'")
        except Exception as e:
            logger.warning(f"Failed to initialize MinIO client: {e}")
            self.client = None

    def check_health(self):
        """Checks MinIO service reachability and default bucket state."""
        if not self.client:
            return {
                "connected": False,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": "Client not initialized"
            }

        # Fast TCP check to prevent urllib3 retry delays if MinIO is not running
        import socket
        try:
            parts = self.endpoint.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else (443 if self.secure else 80)
            with socket.create_connection((host, port), timeout=0.8):
                pass
        except Exception as conn_err:
            logger.debug(f"MinIO port check unreachable: {conn_err}")
            return {
                "connected": False,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": "Unable to connect to MinIO server (host unreachable)",
                "hint": "Ensure local MinIO service is running on the configured endpoint (e.g. minio.exe server ./minio_data)."
            }

        try:
            # Check if bucket exists, or create it if not present
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            if not bucket_exists:
                try:
                    self.client.make_bucket(self.bucket_name)
                    bucket_created = True
                except Exception as b_err:
                    bucket_created = False
                    logger.debug(f"Bucket auto-creation deferred: {b_err}")
            else:
                bucket_created = False

            return {
                "connected": True,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "bucket_exists": bucket_exists or bucket_created,
                "status": "Available"
            }
        except (MaxRetryError, ConnectionRefusedError, OSError) as e:
            logger.debug(f"MinIO connectivity check failed: {e}")
            return {
                "connected": False,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": "Unable to connect to MinIO server",
                "hint": "Ensure local MinIO service is running on the configured endpoint (e.g. minio server ./minio_data)."
            }
        except S3Error as e:
            logger.warning(f"MinIO S3 error: {e}")
            return {
                "connected": False,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": str(e)
            }
        except Exception as e:
            logger.warning(f"Unexpected MinIO error: {e}")
            return {
                "connected": False,
                "type": "MinIO",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": str(e)
            }


# Global storage service instance
storage_service = ObjectStorageService()
