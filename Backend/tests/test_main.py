import io
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure Backend directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a dummy GROQ_API_KEY if not already set, to prevent Pydantic validation errors on startup
os.environ.setdefault("GROQ_API_KEY", "mock_key_for_testing_purposes")

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that the health check endpoint returns 200 and 'ok' status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "modules" in data
    assert "app" in data
    assert "version" in data


def test_process_no_file():
    """Verify that calling process_dataset without a file returns 422 (Unprocessable Entity)."""
    response = client.post("/api/process")
    assert response.status_code == 422


def test_process_unsupported_file_type():
    """Verify that uploading an unsupported file type returns 415 (Unsupported Media Type)."""
    file_content = b"dummy content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/process", files=files)
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_process_empty_file():
    """Verify that uploading an empty file returns 400 (Bad Request)."""
    files = {"file": ("test.csv", io.BytesIO(b""), "text/csv")}
    response = client.post("/api/process", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "empty" in detail or "no columns" in detail or "error reading" in detail
