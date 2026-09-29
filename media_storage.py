"""Media storage contract plus safe local scratch implementation."""
from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4

from content_factory_core import MediaRef

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class MediaStorageAdapter(ABC):
    @abstractmethod
    def put_file(self, source: Path, *, provenance: str, mime_type: Optional[str] = None) -> MediaRef:
        raise NotImplementedError

    @abstractmethod
    def resolve_local(self, media: MediaRef) -> Path:
        raise NotImplementedError


class LocalScratchStorage(MediaStorageAdapter):
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

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
        media_id = str(uuid4())
        safe_name = self._safe_filename(source.name)
        target_dir = (self.root / media_id).resolve()
        if self.root not in target_dir.parents:
            raise ValueError("unsafe storage target")
        target_dir.mkdir(parents=True, exist_ok=False)
        target = target_dir / safe_name
        shutil.copy2(source, target)
        digest = self._sha256(target)
        detected = mime_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        return MediaRef(
            media_id=media_id,
            uri=f"scratch://{media_id}/{safe_name}",
            sha256=digest,
            size_bytes=target.stat().st_size,
            mime_type=detected,
            provenance=provenance,
        )

    def resolve_local(self, media: MediaRef) -> Path:
        prefix = "scratch://"
        if not media.uri.startswith(prefix):
            raise ValueError("media URI does not belong to scratch backend")
        relative = media.uri[len(prefix):]
        candidate = (self.root / relative).resolve()
        if self.root not in candidate.parents or not candidate.is_file():
            raise ValueError("unsafe or missing media URI")
        if self._sha256(candidate) != media.sha256:
            raise ValueError("media integrity check failed")
        return candidate
