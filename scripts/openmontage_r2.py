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
    expires_seconds: int = 86400,
) -> dict[str, Any]:
    if isinstance(expires_seconds, bool) or not isinstance(expires_seconds, int) or not 60 <= expires_seconds <= 604800:
        raise ValueError("Expiry must be 60–604800 seconds")
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

def renew_private_preview(media_id: str, *, storage: R2Storage,
                          expires_seconds: int = 86400) -> dict[str, Any]:
    """Re-sign an existing private OpenMontage object without reuploading."""
    import re
    if not isinstance(media_id, str) or not re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", media_id
    ):
        raise ValueError("Invalid media ID")
    if type(expires_seconds) is not int or not 60 <= expires_seconds <= 604800:
        raise ValueError("Invalid expiry")
    prefix = f"media/{media_id}/"
    response = storage.client.list_objects_v2(Bucket=storage.bucket, Prefix=prefix, MaxKeys=2)
    objects = response.get("Contents", [])
    if len(objects) != 1 or response.get("IsTruncated"):
        raise ValueError("Media not found or ambiguous")
    key = objects[0]["Key"]
    if not key.startswith(prefix) or not key.lower().endswith(".mp4"):
        raise ValueError("Not an OpenMontage MP4")
    metadata = storage.client.head_object(Bucket=storage.bucket, Key=key).get("Metadata", {})
    if metadata.get("media-id") != media_id:
        raise ValueError("Media ID mismatch")
    url = storage.client.generate_presigned_url(
        "get_object", Params={"Bucket": storage.bucket, "Key": key},
        ExpiresIn=expires_seconds, HttpMethod="GET"
    )
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Secure preview link generation failed")
    return {"media_id": media_id, "r2_uri": f"r2://{storage.bucket}/{key}",
            "expires_seconds": expires_seconds, "download_url": url}
