"""
IntelliVault ~ Supabase Object Storage Service
Provides storage adapter for Supabase Storage: upload, download, delete, and health diagnostics.
Replaces the previous MinIO/S3 adapter.
"""

from backend.app.utils.logger import logger


class SupabaseStorageService:
    """Manages file storage operations via Supabase Storage."""

    def __init__(self):
        self._client = None       # supabase.Client (private, backend-only)
        self.bucket_name = None
        self._initialized = False

    def init_app(self, app):
        """Initializes the Supabase client from Flask application configuration."""
        supabase_url = app.config.get("SUPABASE_URL", "")
        service_key = app.config.get("SUPABASE_SERVICE_KEY", "")
        self.bucket_name = app.config.get("SUPABASE_BUCKET_NAME", "intellivault-files")

        if not supabase_url or not service_key:
            logger.warning(
                "Supabase storage client not initialized: SUPABASE_URL or SUPABASE_SERVICE_KEY is missing."
            )
            self._initialized = False
            return

        try:
            from supabase import create_client
            self._client = create_client(supabase_url, service_key)
            self._initialized = True
            logger.info(
                f"Supabase storage client initialized for bucket: '{self.bucket_name}'"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase storage client: {e}")
            self._client = None
            self._initialized = False

    # ------------------------------------------------------------------
    # Storage Operations
    # ------------------------------------------------------------------

    def upload(self, storage_path: str, file_data: bytes, content_type: str = "application/octet-stream") -> None:
        """
        Uploads a file to the private Supabase Storage bucket.

        :param storage_path: Object path within the bucket.
        :param file_data: Raw file bytes.
        :param content_type: MIME type of the file.
        """
        self._client.storage.from_(self.bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": content_type, "upsert": "false"}
        )

    def download(self, storage_path: str) -> bytes:
        """
        Downloads a file from the private Supabase Storage bucket.

        :param storage_path: Object path within the bucket.
        :return: Raw file bytes.
        """
        return self._client.storage.from_(self.bucket_name).download(storage_path)

    def delete(self, storage_path: str) -> None:
        """
        Deletes a file from the private Supabase Storage bucket.

        :param storage_path: Object path within the bucket.
        """
        self._client.storage.from_(self.bucket_name).remove([storage_path])

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    def check_health(self) -> dict:
        """Returns Supabase Storage connection status for the system readiness endpoint."""
        if not self._initialized or not self._client:
            return {
                "connected": False,
                "type": "Supabase Storage",
                "bucket": self.bucket_name,
                "error": "Client not initialized. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.",
            }

        try:
            # Lightweight check: list bucket root items (limit 1)
            self._client.storage.from_(self.bucket_name).list(path="", options={"limit": 1})
            return {
                "connected": True,
                "type": "Supabase Storage",
                "bucket": self.bucket_name,
                "status": "Available",
            }
        except Exception as e:
            logger.debug(f"Supabase storage health check failed: {e}")
            return {
                "connected": False,
                "type": "Supabase Storage",
                "bucket": self.bucket_name,
                "error": str(e),
            }


# Global storage service singleton
storage_service = SupabaseStorageService()
