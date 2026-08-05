"""Pluggable file storage.

Uploaded PDFs and avatars go through this layer instead of touching the
disk directly, so the same code runs on a VPS (local disk) and on a
platform with an ephemeral filesystem like Render (Firebase / Cloud
Storage). Pick the backend with STORAGE_BACKEND=local|firebase.

Documents store a relative *storage key* (e.g. "uploads/<uid>/<uuid>.pdf")
rather than an absolute path, so the value is portable across backends.
Legacy documents that stored an absolute local path still work — the local
backend detects and reads those directly.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("lexassist.storage")


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def load(self, key: str) -> bytes | None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class LocalStorage(StorageBackend):
    """Disk storage under a single root. Keys are relative; an absolute key
    is treated as a legacy stored_path and read as-is for backward compat."""

    def __init__(self, root: str):
        self._root = Path(root)

    def _resolve(self, key: str) -> Path:
        if os.path.isabs(key):
            return Path(key)  # legacy absolute stored_path
        return self._root / key

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def load(self, key: str) -> bytes | None:
        path = self._resolve(key)
        if not path.exists():
            return None
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        try:
            self._resolve(key).unlink(missing_ok=True)
        except OSError:
            pass  # already gone / permission — callers proceed regardless


class FirebaseStorage(StorageBackend):
    """Firebase Storage (a Google Cloud Storage bucket). The blocking GCS
    client runs in a worker thread so it never blocks the event loop."""

    def __init__(self, bucket_name: str, credentials_json: str):
        from google.cloud import storage as gcs
        from google.oauth2 import service_account

        info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(info)
        self._client = gcs.Client(project=info.get("project_id"), credentials=credentials)
        self._bucket = self._client.bucket(bucket_name)

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        def _upload() -> None:
            self._bucket.blob(key).upload_from_string(data, content_type=content_type)

        await asyncio.to_thread(_upload)

    async def load(self, key: str) -> bytes | None:
        def _download() -> bytes | None:
            blob = self._bucket.blob(key)
            if not blob.exists():
                return None
            return blob.download_as_bytes()

        return await asyncio.to_thread(_download)

    async def delete(self, key: str) -> None:
        def _delete() -> None:
            try:
                self._bucket.blob(key).delete()
            except Exception:  # already gone / not found
                pass

        await asyncio.to_thread(_delete)


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        if settings.storage_backend.strip().lower() == "firebase":
            logger.info("Storage backend: Firebase (bucket=%s)", settings.firebase_bucket)
            _storage = FirebaseStorage(settings.firebase_bucket, settings.firebase_credentials_json)
        else:
            logger.info("Storage backend: local disk (%s)", settings.storage_root)
            _storage = LocalStorage(settings.storage_root)
    return _storage
