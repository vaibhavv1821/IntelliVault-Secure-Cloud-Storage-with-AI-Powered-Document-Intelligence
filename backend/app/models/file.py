"""
IntelliVault ~ File Metadata Model & Schema
Defines the database schema and domain model for uploaded files in MongoDB.
"""

from datetime import datetime, timezone
from bson import ObjectId

# Maximum allowable file size for basic storage uploads (50 MB)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


class FileMetadata:
    """
    FileMetadata entity representing an uploaded file record in IntelliVault.
    Encapsulates schema validation, normalization, and MongoDB serialization.
    """

    def __init__(
        self,
        user_id: ObjectId | str,
        original_name: str,
        storage_key: str,
        content_type: str = "application/octet-stream",
        size: int = 0,
        _id: ObjectId | str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None
    ):
        self._id = ObjectId(_id) if isinstance(_id, str) and ObjectId.is_valid(_id) else (_id or ObjectId())
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
        if not isinstance(self.user_id, ObjectId):
            raise ValueError("user_id must be a valid ObjectId or ObjectId hex string.")

        self.original_name = self.validate_original_name(original_name)
        self.storage_key = self.validate_storage_key(storage_key)
        self.content_type = self.validate_content_type(content_type)
        self.size = self.validate_size(size)

        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @staticmethod
    def validate_original_name(name: str) -> str:
        """Validates that original_name is non-empty and within reasonable length."""
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("original_name must be a non-empty string.")
        trimmed = name.strip()
        if len(trimmed) > 255:
            raise ValueError("original_name cannot exceed 255 characters.")
        return trimmed

    @staticmethod
    def validate_storage_key(key: str) -> str:
        """Validates that storage_key is a non-empty string."""
        if not key or not isinstance(key, str) or not key.strip():
            raise ValueError("storage_key must be a non-empty string.")
        return key.strip()

    @staticmethod
    def validate_content_type(content_type: str) -> str:
        """Validates and trims MIME content type."""
        if not content_type or not isinstance(content_type, str) or not content_type.strip():
            return "application/octet-stream"
        return content_type.strip().lower()

    @staticmethod
    def validate_size(size: int) -> int:
        """Validates that size is a non-negative integer within storage limits."""
        if not isinstance(size, int) or size < 0:
            raise ValueError("size must be a non-negative integer.")
        if size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES} bytes (50 MB).")
        return size

    def to_db_dict(self) -> dict:
        """Serializes the file metadata entity for MongoDB document storage."""
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "original_name": self.original_name,
            "storage_key": self.storage_key,
            "content_type": self.content_type,
            "size": self.size,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def to_dict(self) -> dict:
        """
        Serializes file metadata entity for client JSON API responses.
        Converts ObjectIds and datetimes to standard JSON types.
        """
        return {
            "id": str(self._id),
            "user_id": str(self.user_id),
            "original_name": self.original_name,
            "storage_key": self.storage_key,
            "content_type": self.content_type,
            "size": self.size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_db(cls, doc: dict):
        """Constructs a FileMetadata entity from a raw MongoDB document."""
        if not doc:
            return None
        return cls(
            _id=doc.get("_id"),
            user_id=doc.get("user_id"),
            original_name=doc.get("original_name"),
            storage_key=doc.get("storage_key"),
            content_type=doc.get("content_type", "application/octet-stream"),
            size=doc.get("size", 0),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at")
        )

    def __repr__(self) -> str:
        return f"<FileMetadata id={self._id} name='{self.original_name}' size={self.size}>"
