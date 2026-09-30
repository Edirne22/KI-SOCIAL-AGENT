"""Cloudflare R2 / S3-compatible media storage adapter.

The adapter deliberately accepts an injected S3-compatible client. Production
may use boto3 or another compatible SDK without coupling the domain layer to it.
"""
from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Optional, Protocol
from uuid import uuid4

from content_factory_core import MediaRef
from media_storage import MediaStorageAdapter

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class S3CompatibleClient(Protocol):
    def upload_file(self, filename: str, bucket: str, key: str, ExtraArgs: Optional[dict] = None) -> None:
        ...
    def download_file(self, bucket: str, key: str, filename: str) -> None:
        ...


class R2Storage(MediaStorageAdapter):
    def __init__(
        self, client: S3CompatibleClient, *, bucket: str, scratch_root: Path,
        prefix: str = "content-factory", max_size_bytes: int = 2 * 1024 * 1024 * 1024,
    ):
        if not bucket.strip():
            raise ValueError("R2 bucket is required")
        if max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")
        self.client = client
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.scratch_root = Path(scratch_root).resolve()
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_bytes

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _safe_filename(name: str) -> str:
        cleaned = _SAFE_NAME.sub("_", Path(name).name).strip("._")
        return cleaned or "media.bin"

    def put_file(self, source: Path, *, provenance: str, mime_type: Optional[str] = None) -> MediaRef:
        source = Path(source).resolve(strict=True)
        if not source.is_file():
            raise ValueError("source must be a regular file")
        size = source.stat().st_size
        if size > self.max_size_bytes:
            raise ValueError("media exceeds configured R2 size limit")
        safe_name = self._safe_filename(source.name)
        media_id = str(uuid4())
        key = "/".join(part for part in (self.prefix, media_id, safe_name) if part)
        detected = mime_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        digest = self._sha256(source)
        self.client.upload_file(
            str(source), self.bucket, key,
            ExtraArgs={"ContentType": detected, "Metadata": {"sha256": digest}},
        )
        return MediaRef(
            media_id=media_id,
            uri=f"r2://{self.bucket}/{key}",
            sha256=digest,
            size_bytes=size,
            mime_type=detected,
            provenance=provenance,
        )

    def resolve_local(self, media: MediaRef) -> Path:
        prefix = f"r2://{self.bucket}/"
        if not media.uri.startswith(prefix):
            raise ValueError("media URI does not belong to configured R2 bucket")
        key = media.uri[len(prefix):]
        if not key or key.startswith("/") or ".." in Path(key).parts:
            raise ValueError("unsafe R2 object key")
        target_dir = (self.scratch_root / media.media_id).resolve()
        if self.scratch_root not in target_dir.parents:
            raise ValueError("unsafe scratch target")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / self._safe_filename(Path(key).name)).resolve()
        if self.scratch_root not in target.parents:
            raise ValueError("unsafe scratch target")
        self.client.download_file(self.bucket, key, str(target))
        if not target.is_file():
            raise ValueError("R2 client did not materialize media")
        if target.stat().st_size != media.size_bytes or self._sha256(target) != media.sha256:
            target.unlink(missing_ok=True)
            raise ValueError("R2 media integrity check failed")
        return target
