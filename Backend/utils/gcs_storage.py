"""
utils/gcs_storage.py
====================
Unified storage layer.
- STORAGE_BACKEND=local  → local disk (dev, default)
- STORAGE_BACKEND=gcs    → Google Cloud Storage (production)
"""
import os
import io
import json
import joblib
from typing import Any
from dotenv import load_dotenv

load_dotenv()

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "ai-career-artifacts")


def _get_gcs_client():
    """Lazy-import GCS client to avoid errors in local mode."""
    from google.cloud import storage
    return storage.Client()


def save_pickle(obj: Any, path: str) -> str:
    """Save a Python object (.pkl) to local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        buffer = io.BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_file(buffer, content_type="application/octet-stream")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump(obj, path)
    return path


def load_pickle(path: str) -> Any:
    """Load a .pkl file from local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        buffer = io.BytesIO()
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).download_to_file(buffer)
        buffer.seek(0)
        return joblib.load(buffer)
    return joblib.load(path)


def save_json(data: dict, path: str) -> str:
    """Save a dict as JSON to local disk or GCS."""
    content = json.dumps(data, indent=2, default=str).encode("utf-8")
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_string(content, content_type="application/json")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.decode())
    return path


def load_json(path: str) -> dict:
    """Load a JSON file from local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        return json.loads(bucket.blob(path).download_as_text())
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(df, path: str) -> str:
    """Save a pandas DataFrame as CSV to local disk or GCS."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_string(csv_bytes, content_type="text/csv")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(csv_bytes)
    return path


def generate_signed_url(path: str, expires_minutes: int = 60) -> str:
    """
    Generate a temporary download URL for a GCS file.
    Returns local path string in local mode.
    """
    if STORAGE_BACKEND == "gcs":
        import datetime
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(path)
        return blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=expires_minutes),
            method="GET",
        )
    return f"/downloads/{os.path.basename(path)}"


def cleanup_old_local_files(max_age_minutes: int = 60) -> None:
    """
    Scans local 'exports' and 'artifacts' folders and deletes files older than max_age_minutes.
    Only executes in 'local' backend mode to prevent local disk bloat.
    """
    if STORAGE_BACKEND != "local":
        return

    import time
    from pathlib import Path

    now = time.time()
    max_age_seconds = max_age_minutes * 60

    for folder_name in ["exports", "artifacts"]:
        folder = Path(folder_name)
        if not folder.exists() or not folder.is_dir():
            continue

        for file_path in folder.glob("**/*"):
            if file_path.is_file():
                # Check modification time of file
                file_age = now - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        print(f"[Cleanup] Deleted old local file: {file_path}")
                    except Exception as e:
                        print(f"[Cleanup] Error deleting {file_path}: {e}")
