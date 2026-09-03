"""
IntelliVault ~ Central Configuration Module
Loads and parses environment variables with strict defaults and typing.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env from project root if available
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=env_path)


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "intellivault-default-insecure-secret-key")
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/intellivault")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "intellivault")
    MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", 2000))

    # MinIO / S3 Object Storage
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "intellivault-files")
    MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1", "t")

    # JWT Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "intellivault-jwt-signing-secret")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_ACCESS_TOKEN_EXPIRES_HOURS)

    # Master Encryption Key for AES-256 GCM
    MASTER_ENCRYPTION_KEY = os.getenv(
        "MASTER_ENCRYPTION_KEY",
        "dGhpc2lzYTMyeWJ5dGVzZWNyZXRrZXlmb3JkZXZlbG9wbWVudCE="
    )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    MONGODB_DB_NAME = "intellivault_test"
    MINIO_BUCKET_NAME = "intellivault-test-files"


class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure sensitive keys are explicitly set
    if os.getenv("SECRET_KEY") == "intellivault-default-insecure-secret-key":
        raise ValueError("SECRET_KEY must be explicitly defined in production environment.")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
