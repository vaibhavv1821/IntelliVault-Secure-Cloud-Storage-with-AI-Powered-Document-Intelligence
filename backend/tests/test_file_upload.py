"""
IntelliVault ~ File Metadata & Upload API Tests (Phase 1 ~ Step 5)
Verifies:
1. Valid file upload via multipart/form-data (HTTP 201)
2. Metadata persistence in MongoDB
3. MinIO binary stream put_object invocation
4. Public payload sanitization (no sensitive leakage)
5. Missing/invalid token rejection (HTTP 401)
6. Missing file part rejection (HTTP 400)
7. Empty filename rejection (HTTP 400)
8. File size ceiling enforcement (HTTP 400)
9. Storage key collision resistance (UUID prefixes)
10. Authenticated user files listing (GET /api/files)
11. Multi-user file isolation
12. MinIO rollback cleanup on MongoDB persistence failure
"""

import io
from unittest.mock import MagicMock
import pytest
import mongomock
from bson import ObjectId

from backend.app import create_app
from backend.app.models.user import User
from backend.app.services.db import db_service
from backend.app.services.storage import storage_service
from backend.app.utils.security import hash_password, generate_access_token


class MockMinioClient:
    """In-memory mock for MinIO object storage client."""

    def __init__(self):
        self.objects = {}
        self.put_object_calls = []
        self.remove_object_calls = []

    def put_object(self, bucket_name, object_name, data, length, content_type="application/octet-stream"):
        content = data.read(length) if hasattr(data, "read") else data
        self.objects[(bucket_name, object_name)] = {
            "content": content,
            "length": length,
            "content_type": content_type
        }
        self.put_object_calls.append({
            "bucket": bucket_name,
            "key": object_name,
            "length": length,
            "content_type": content_type
        })
        return MagicMock()

    def remove_object(self, bucket_name, object_name):
        self.remove_object_calls.append({
            "bucket": bucket_name,
            "key": object_name
        })
        self.objects.pop((bucket_name, object_name), None)


@pytest.fixture
def file_client():
    """Provides test client with in-memory MongoDB and mocked MinIO client."""
    app = create_app(config_name="testing")

    mock_db_client = mongomock.MongoClient()
    mock_db = mock_db_client["intellivault_test"]

    original_db_client = db_service.client
    original_db = db_service.db
    db_service.client = mock_db_client
    db_service.db = mock_db

    mock_minio = MockMinioClient()
    original_minio_client = storage_service.client
    storage_service.client = mock_minio

    # Seed User A (Alice)
    alice = User(
        name="Alice Architect",
        email="alice@intellivault.dev",
        password_hash=hash_password("AliceVault#2026!"),
        role="member",
        status="active"
    )
    mock_db["users"].insert_one(alice.to_db_dict())

    # Seed User B (Bob)
    bob = User(
        name="Bob Builder",
        email="bob@intellivault.dev",
        password_hash=hash_password("BobVault#2026!"),
        role="member",
        status="active"
    )
    mock_db["users"].insert_one(bob.to_db_dict())

    with app.test_client() as client:
        yield client, alice, bob, mock_minio, mock_db, app

    # Cleanup singletons
    db_service.client = original_db_client
    db_service.db = original_db
    storage_service.client = original_minio_client


def create_auth_token(user, app):
    """Helper to generate JWT bearer token for a seeded user."""
    return generate_access_token(
        user_id=str(user._id),
        email=user.email,
        role=user.role,
        secret_key=app.config["JWT_SECRET_KEY"],
        expires_in_seconds=3600
    )


def test_upload_file_success(file_client):
    """Test 1: Valid multipart file upload returns HTTP 201 with complete sanitized metadata."""
    client, alice, _, mock_minio, _, app = file_client
    token = create_auth_token(alice, app)

    file_content = b"Hello IntelliVault! This is an authenticated test document."
    data = {
        "file": (io.BytesIO(file_content), "project_specs.txt", "text/plain")
    }

    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["message"] == "File uploaded successfully."
    assert "data" in payload
    assert "file" in payload["data"]

    f = payload["data"]["file"]
    assert f["original_name"] == "project_specs.txt"
    assert f["user_id"] == str(alice._id)
    assert f["size"] == len(file_content)
    assert f["content_type"] == "text/plain"
    assert f["storage_key"].startswith(f"user-files/{alice._id}/")
    assert f["storage_key"].endswith("_project_specs.txt")
    assert "id" in f
    assert "created_at" in f


def test_upload_persists_in_mongodb(file_client):
    """Test 2: Uploaded file record is stored accurately in the MongoDB 'files' collection."""
    client, alice, _, _, mock_db, app = file_client
    token = create_auth_token(alice, app)

    data = {
        "file": (io.BytesIO(b"MongoDB Persistence Test Content"), "db_test.pdf", "application/pdf")
    }

    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    file_id = response.get_json()["data"]["file"]["id"]

    db_doc = mock_db["files"].find_one({"_id": ObjectId(file_id)})
    assert db_doc is not None
    assert db_doc["original_name"] == "db_test.pdf"
    assert db_doc["user_id"] == alice._id
    assert db_doc["size"] == len(b"MongoDB Persistence Test Content")
    assert db_doc["content_type"] == "application/pdf"


def test_upload_invokes_minio_put_object(file_client):
    """Test 3: File binary stream is transmitted to MinIO with correct bucket and parameters."""
    client, alice, _, mock_minio, _, app = file_client
    token = create_auth_token(alice, app)

    payload_bytes = b"Raw binary stream content for MinIO test"
    data = {
        "file": (io.BytesIO(payload_bytes), "minio_stream.csv", "text/csv")
    }

    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    assert len(mock_minio.put_object_calls) == 1
    call = mock_minio.put_object_calls[0]
    assert call["bucket"] == app.config["MINIO_BUCKET_NAME"]
    assert call["length"] == len(payload_bytes)
    assert call["content_type"] == "text/csv"
    assert call["key"].startswith(f"user-files/{alice._id}/")


def test_upload_zero_credential_leak(file_client):
    """Test 4: Response does not leak server secrets, passwords, or MinIO secret keys."""
    client, alice, _, _, _, app = file_client
    token = create_auth_token(alice, app)

    data = {
        "file": (io.BytesIO(b"Confidential test"), "confidential.txt", "text/plain")
    }

    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    text_content = response.get_data(as_text=True)

    assert "password" not in text_content
    assert "password_hash" not in text_content
    assert "minioadmin" not in text_content
    assert "JWT_SECRET_KEY" not in text_content


def test_upload_without_token_fails(file_client):
    """Test 5: POST /api/files/upload without Authorization header returns HTTP 401."""
    client, _, _, _, _, _ = file_client

    data = {
        "file": (io.BytesIO(b"Data"), "unauthorized.txt", "text/plain")
    }
    response = client.post("/api/files/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "MISSING_TOKEN"


def test_upload_without_file_part_fails(file_client):
    """Test 6: POST /api/files/upload with no 'file' field in multipart form returns HTTP 400."""
    client, alice, _, _, _, app = file_client
    token = create_auth_token(alice, app)

    data = {
        "other_field": "some text"
    }
    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "NO_FILE_PART"


def test_upload_empty_filename_fails(file_client):
    """Test 7: POST /api/files/upload with empty filename returns HTTP 400."""
    client, alice, _, _, _, app = file_client
    token = create_auth_token(alice, app)

    data = {
        "file": (io.BytesIO(b"Data"), "", "text/plain")
    }
    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "NO_FILE_SELECTED"


def test_upload_file_too_large_fails(file_client, monkeypatch):
    """Test 8: Upload exceeding MAX_FILE_SIZE_BYTES returns HTTP 400."""
    client, alice, _, _, _, app = file_client
    token = create_auth_token(alice, app)

    # Monkeypatch MAX_FILE_SIZE_BYTES to 10 bytes for test efficiency
    import backend.app.models.file as file_model_mod
    import backend.app.services.file_service as file_service_mod
    monkeypatch.setattr(file_model_mod, "MAX_FILE_SIZE_BYTES", 10)
    monkeypatch.setattr(file_service_mod, "MAX_FILE_SIZE_BYTES", 10)

    data = {
        "file": (io.BytesIO(b"This string is much longer than 10 bytes"), "oversize.txt", "text/plain")
    }
    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "FILE_VALIDATION_ERROR"


def test_unique_storage_keys_for_duplicate_names(file_client):
    """Test 9: Identical original filenames uploaded twice receive distinct UUID storage keys."""
    client, alice, _, mock_minio, _, app = file_client
    token = create_auth_token(alice, app)

    data1 = {"file": (io.BytesIO(b"First version"), "notes.txt", "text/plain")}
    res1 = client.post("/api/files/upload", data=data1, content_type="multipart/form-data",
                       headers={"Authorization": f"Bearer {token}"})
    key1 = res1.get_json()["data"]["file"]["storage_key"]

    data2 = {"file": (io.BytesIO(b"Second version"), "notes.txt", "text/plain")}
    res2 = client.post("/api/files/upload", data=data2, content_type="multipart/form-data",
                       headers={"Authorization": f"Bearer {token}"})
    key2 = res2.get_json()["data"]["file"]["storage_key"]

    assert key1 != key2
    assert len(mock_minio.put_object_calls) == 2


def test_get_files_list_success(file_client):
    """Test 10: GET /api/files returns authenticated user's uploaded files list."""
    client, alice, _, _, _, app = file_client
    token = create_auth_token(alice, app)

    # Upload two files for Alice
    client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"Doc 1"), "doc1.txt", "text/plain")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"Doc 2"), "doc2.txt", "text/plain")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get("/api/files", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    files = payload["data"]["files"]
    assert len(files) == 2
    names = [f["original_name"] for f in files]
    assert "doc1.txt" in names
    assert "doc2.txt" in names


def test_user_files_isolation(file_client):
    """Test 11: Multi-tenant file isolation: User A cannot see User B's files."""
    client, alice, bob, _, _, app = file_client
    alice_token = create_auth_token(alice, app)
    bob_token = create_auth_token(bob, app)

    # Alice uploads a secret file
    client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"Alice Secret File"), "alice_plans.pdf", "application/pdf")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {alice_token}"}
    )

    # Bob uploads a blueprint file
    client.post(
        "/api/files/upload",
        data={"file": (io.BytesIO(b"Bob Blueprint File"), "bob_blueprint.png", "image/png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {bob_token}"}
    )

    # Verify Alice only sees her own file
    alice_res = client.get("/api/files", headers={"Authorization": f"Bearer {alice_token}"})
    alice_files = alice_res.get_json()["data"]["files"]
    assert len(alice_files) == 1
    assert alice_files[0]["original_name"] == "alice_plans.pdf"

    # Verify Bob only sees his own file
    bob_res = client.get("/api/files", headers={"Authorization": f"Bearer {bob_token}"})
    bob_files = bob_res.get_json()["data"]["files"]
    assert len(bob_files) == 1
    assert bob_files[0]["original_name"] == "bob_blueprint.png"


def test_mongodb_failure_rolls_back_minio(file_client, monkeypatch):
    """Test 12: If MongoDB fails after MinIO put_object, MinIO remove_object is called (no orphan blobs)."""
    client, alice, _, mock_minio, mock_db, app = file_client
    token = create_auth_token(alice, app)

    # Force insert_one on files collection to raise an exception
    def failing_insert(doc):
        raise RuntimeError("Database connection suddenly dropped!")

    monkeypatch.setattr(mock_db["files"], "insert_one", failing_insert)

    data = {
        "file": (io.BytesIO(b"Rollback test payload"), "rollback.txt", "text/plain")
    }
    response = client.post(
        "/api/files/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "STORAGE_ERROR"

    # MinIO put_object was called initially
    assert len(mock_minio.put_object_calls) == 1
    uploaded_key = mock_minio.put_object_calls[0]["key"]

    # Verify rollback: remove_object was called for the uploaded object key
    assert len(mock_minio.remove_object_calls) == 1
    assert mock_minio.remove_object_calls[0]["key"] == uploaded_key
