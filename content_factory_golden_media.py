"""Block 8: verify real private media bytes before issuing a Golden Tablet.

No public URLs, new network API, or publishing occurs here. Production injects
the existing private R2Storage; tests inject LocalScratchStorage.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob
from content_factory_golden_tablet import (
    FinalQMReport, GoldenTablet, GoldenTabletError, present_golden_tablet,
)
from media_storage import MediaStorageAdapter


@dataclass(frozen=True)
class VerifiedMedia:
    media_id: str
    uri: str
    sha256: str
    size_bytes: int
    mime_type: str


@dataclass(frozen=True)
class VerifiedGoldenPreview:
    tablet: GoldenTablet
    media: tuple[VerifiedMedia, ...]


def present_verified_golden_tablet(
    job: ProductionJob,
    report: FinalQMReport,
    *,
    storage: MediaStorageAdapter,
    allowed_uri_prefixes: tuple[str, ...] = ("r2://",),
    max_media_bytes: int = 2 * 1024 * 1024 * 1024,
) -> VerifiedGoldenPreview:
    """Fail closed if any media is missing, altered or outside its private store.

    This is the production-oriented entrypoint. A passing FinalQMReport is a
    prerequisite, NOT a substitute for checking media bytes. Checks finish
    before calling present_golden_tablet, which changes job status.
    """
    if job.status != JobStatus.QM or report.job_id != job.job_id or report.revision != job.revision:
        raise GoldenTabletError("media check requires matching job in QM")
    if not report.passed:
        raise GoldenTabletError("failed final QM cannot reach preview")
    if not allowed_uri_prefixes or any(not p for p in allowed_uri_prefixes):
        raise GoldenTabletError("allowed private URI prefixes required")
    if max_media_bytes <= 0:
        raise GoldenTabletError("invalid media size limit")
    if not job.media:
        raise GoldenTabletError("media preview requires an actual output asset")

    before = job.approval_manifest()
    seen: set[str] = set()
    verified: list[VerifiedMedia] = []
    for ref in job.media:
        if ref.media_id in seen:
            raise GoldenTabletError("duplicate media id")
        seen.add(ref.media_id)
        if not ref.uri.startswith(allowed_uri_prefixes):
            raise GoldenTabletError("media does not use the authorized private storage")
        if ref.size_bytes <= 0 or ref.size_bytes > max_media_bytes:
            raise GoldenTabletError("invalid preview media size")
        if not ref.mime_type.startswith(("video/", "image/", "audio/")):
            raise GoldenTabletError("unsupported preview media type")
        try:
            actual = Path(storage.resolve_local(ref))
            if not actual.is_file() or actual.stat().st_size != ref.size_bytes:
                raise ValueError("media missing or size mismatch")
            digest = hashlib.sha256()
            with actual.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != ref.sha256:
                raise ValueError("media hash mismatch")
        except Exception as exc:
            raise GoldenTabletError("private media retrieval/integrity failed") from exc
        verified.append(VerifiedMedia(ref.media_id, ref.uri, ref.sha256, ref.size_bytes, ref.mime_type))

    if job.approval_manifest() != before or job.status != JobStatus.QM:
        raise GoldenTabletError("media or job changed during verification")
    tablet = present_golden_tablet(job, report)
    if tablet.manifest != job.approval_manifest() or set(tablet.media_ids) != seen:
        raise GoldenTabletError("preview manifest changed after verification")
    return VerifiedGoldenPreview(tablet, tuple(verified))
