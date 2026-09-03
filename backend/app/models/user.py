"""
IntelliVault ~ User Model & Schema
Defines the database schema and domain model for user accounts in MongoDB.
"""

from datetime import datetime, timezone
import re
from bson import ObjectId

# Regex for standard RFC 5322-compliant email format validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Permitted user roles within the IntelliVault RBAC framework
VALID_ROLES = {"admin", "member", "viewer"}
DEFAULT_ROLE = "member"

# Permitted user account statuses
VALID_STATUSES = {"active", "suspended", "pending"}
DEFAULT_STATUS = "active"


class User:
    """
    User entity representing an authenticated identity in IntelliVault.
    Encapsulates schema validation, normalization, and MongoDB serialization.
    """

    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = DEFAULT_ROLE,
        status: str = DEFAULT_STATUS,
        _id: ObjectId | str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        last_login_at: datetime | None = None
    ):
        self._id = ObjectId(_id) if isinstance(_id, str) and ObjectId.is_valid(_id) else (_id or ObjectId())
        self.name = self.validate_name(name)
        self.email = self.validate_and_normalize_email(email)
        self.password_hash = self.validate_password_hash(password_hash)
        self.role = self.validate_role(role)
        self.status = self.validate_status(status)

        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.last_login_at = last_login_at

    @staticmethod
    def validate_name(name: str) -> str:
        """Validates and trims user display name."""
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("User name must be a non-empty string.")
        trimmed = name.strip()
        if len(trimmed) < 2 or len(trimmed) > 100:
            raise ValueError("User name must be between 2 and 100 characters.")
        return trimmed

    @staticmethod
    def validate_and_normalize_email(email: str) -> str:
        """Normalizes email to lowercase, strips whitespace, and validates format."""
        if not email or not isinstance(email, str) or not email.strip():
            raise ValueError("Email must be a non-empty string.")
        normalized = email.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError(f"Invalid email address format: '{normalized}'.")
        return normalized

    @staticmethod
    def validate_password_hash(password_hash: str) -> str:
        """Verifies that the password hash is present and not empty."""
        if not password_hash or not isinstance(password_hash, str) or not password_hash.strip():
            raise ValueError("Password hash must be a non-empty string.")
        return password_hash.strip()

    @staticmethod
    def validate_role(role: str) -> str:
        """Ensures the role belongs to valid RBAC roles."""
        if not role or role not in VALID_ROLES:
            raise ValueError(f"Invalid role: '{role}'. Must be one of {sorted(VALID_ROLES)}.")
        return role

    @staticmethod
    def validate_status(status: str) -> str:
        """Ensures account status is valid."""
        if not status or status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: '{status}'. Must be one of {sorted(VALID_STATUSES)}.")
        return status

    def to_db_dict(self) -> dict:
        """Serializes the user entity for MongoDB document storage."""
        return {
            "_id": self._id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login_at": self.last_login_at
        }

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Serializes user object for API responses.
        Excludes password_hash by default to maintain zero-leakage security.
        """
        data = {
            "id": str(self._id),
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    @classmethod
    def from_db(cls, doc: dict):
        """Constructs a User entity from a raw MongoDB document."""
        if not doc:
            return None
        return cls(
            name=doc.get("name"),
            email=doc.get("email"),
            password_hash=doc.get("password_hash"),
            role=doc.get("role", DEFAULT_ROLE),
            status=doc.get("status", DEFAULT_STATUS),
            _id=doc.get("_id"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            last_login_at=doc.get("last_login_at")
        )

    def __repr__(self) -> str:
        return f"<User id={self._id} email='{self.email}' role='{self.role}'>"
