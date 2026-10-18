"""B72C: owner-authorized Telegram album to B72B local media staging.

This does not render, publish, or create any public URL.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

from scripts.openmontage_private_media_stage import stage_private_scenes


def stage_owner_album(client, bucket, *, job_id, owner_chat, authorized_chat,
                      selections, destination):
    """Read only an album indexed to the configured Telegram owner."""
    if (not authorized_chat or str(owner_chat) != str(authorized_chat)
            or not isinstance(job_id, str)
            or not re.fullmatch(r"tgalbum[a-f0-9]{32}", job_id)):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: owner or album identity invalid")
    index_key = "private/v1/telegram-album-index/" + job_id + ".json"
    raw = client.get_object(Bucket=bucket, Key=index_key)["Body"].read(8193)
    if len(raw) > 8192:
        raise ValueError("PRIVATE_MEDIA_INVALID: album index too large")
    index = json.loads(raw)
    owner_hash = sha256(str(owner_chat).encode()).hexdigest()
    if (index.get("job_id") != job_id or index.get("lane") != "private"
            or index.get("owner_hash") != owner_hash):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: album index ownership mismatch")
    from datetime import datetime
    from scripts.r2_media_warehouse import job_prefix
    created = datetime.fromisoformat(index["created_at"])
    prefix = job_prefix("private", created, job_id)
    manifest_raw = client.get_object(Bucket=bucket, Key=prefix + "manifest.json")["Body"].read(65537)
    if len(manifest_raw) > 65536:
        raise ValueError("PRIVATE_MEDIA_INVALID: manifest too large")
    manifest = json.loads(manifest_raw)
    if manifest.get("job_id") != job_id or manifest.get("prefix") != prefix:
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: manifest identity mismatch")
    return stage_private_scenes(client, bucket, manifest, selections, destination)
