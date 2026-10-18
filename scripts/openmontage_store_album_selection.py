"""Explicit owner-authorized scene selection for an existing private album.

No implicit rights grant, no public link, no social publishing.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re


def store_album_selection(client, bucket, *, request_id, album_job_id,
                          owner_chat, authorized_chat, selections):
    if (not authorized_chat or str(owner_chat) != str(authorized_chat)
            or not re.fullmatch(r"tg-[0-9]+", request_id)
            or not re.fullmatch(r"tgalbum[a-f0-9]{32}", album_job_id)):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: owner or request invalid")
    if (not isinstance(selections, list) or not 1 <= len(selections) <= 8
            or any(not isinstance(s, dict) or
                   set(s) != {"scene_number", "asset_id", "media_license", "rights_verified"}
                   or s["scene_number"] != i
                   or not isinstance(s["asset_id"], str)
                   or not re.fullmatch(r"[A-Za-z0-9_-]{10,64}", s["asset_id"])
                   or s["media_license"] not in
                   {"owned_content", "cc0", "public_domain", "explicit_permission_granted"}
                   or s["rights_verified"] is not True
                   for i, s in enumerate(selections, 1))):
        raise ValueError("PRIVATE_MEDIA_INVALID: explicit scene rights required")
    index_key = f"private/v1/telegram-album-index/{album_job_id}.json"
    index_raw = client.get_object(Bucket=bucket, Key=index_key)["Body"].read(8193)
    if len(index_raw) > 8192:
        raise ValueError("PRIVATE_MEDIA_INVALID: oversized index")
    index = json.loads(index_raw)
    if (index.get("job_id") != album_job_id or index.get("lane") != "private"
            or index.get("owner_hash") != sha256(str(owner_chat).encode()).hexdigest()):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: album not owned by requester")
    record = {"request_id": request_id, "album_job_id": album_job_id,
              "scenes": selections}
    payload = json.dumps(record, sort_keys=True).encode()
    if len(payload) > 32768:
        raise ValueError("PRIVATE_MEDIA_INVALID: oversized selection")
    key = f"openmontage/album-selections/{request_id}.json"
    client.put_object(Bucket=bucket, Key=key, Body=payload,
                      ContentType="application/json", IfNoneMatch="*")
    return {"request_id": request_id, "album_job_id": album_job_id,
            "selected_scenes": len(selections)}
