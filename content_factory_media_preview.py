"""Private Block-6 media preview boundary.

R2 stays private. A preview is materialized through the existing storage adapter,
verified there against MediaRef size/SHA-256, then delivered only to the already
allowlisted Telegram chat. This module never publishes to a social platform.
"""
from __future__ import annotations
from content_factory_core import MediaRef
from media_storage import MediaStorageAdapter


class MediaPreviewError(RuntimeError):
    pass


def send_telegram_preview(media: MediaRef, storage: MediaStorageAdapter, *, caption: str = ""):
    if not media.mime_type.startswith(("video/", "image/")):
        raise MediaPreviewError("preview supports image/video media only")
    local = storage.resolve_local(media)
    # resolve_local is the integrity boundary: R2Storage checks size + SHA-256,
    # LocalScratchStorage checks SHA-256 before this point.
    if media.mime_type.startswith("video/"):
        from telegram_bot import send_video
        return send_video(local, caption=caption)
    from telegram_bot import send_photo
    return send_photo(local, caption=caption)
