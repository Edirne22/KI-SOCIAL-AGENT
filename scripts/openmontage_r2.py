"""Private OpenMontage MP4 upload using the repository's existing R2Storage.

Presigned links are bearer credentials: never print, log, or commit them.
No public ACL, publishing, or Telegram dispatch is performed here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from media_storage import R2Storage


def upload_private_preview(
    path: Path,
    *,
    storage: R2Storage,
    expires_seconds: int = 900,
) -> dict[str, Any]:
    if isinstance(expires_seconds, bool) or not isinstance(expires_seconds, int) or not 60 <= expires_seconds <= 3600:
        raise ValueError("Expiry must be 60–3600 seconds")
    source = Path(path).resolve(strict=True)
    if not source.is_file() or source.suffix.lower() != ".mp4" or source.stat().st_size == 0:
        raise ValueError("A non-empty local MP4 file is required")
    media = storage.put_file(source, provenance="openmontage-private-preview", mime_type="video/mp4")
    key = storage._object_key(media)
    url = storage.client.generate_presigned_url(
        "get_object",
        Params={"Bucket": storage.bucket, "Key": key},
        ExpiresIn=expires_seconds,
        HttpMethod="GET",
    )
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Unable to generate a secure preview URL")
    return {
        "media_id": media.media_id,
        "r2_uri": media.uri,
        "expires_seconds": expires_seconds,
        "download_url": url,
    }
