"""Read-only preflight for a private OpenMontage album production request."""
import re
from hashlib import sha256
import json


def preflight_album(client, bucket, *, request_id, album_job_id,
                    owner_chat, authorized_chat):
    if (not authorized_chat or str(owner_chat) != str(authorized_chat)
            or not re.fullmatch(r"tg-[0-9]+", request_id)
            or not re.fullmatch(r"tgalbum[a-f0-9]{32}", album_job_id)):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED")
    index_key = "private/v1/telegram-album-index/" + album_job_id + ".json"
    index = json.loads(client.get_object(Bucket=bucket, Key=index_key)["Body"].read(8193))
    if (index.get("job_id") != album_job_id or index.get("lane") != "private"
            or index.get("owner_hash") != sha256(str(owner_chat).encode()).hexdigest()):
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED")
    key = "openmontage/album-selections/" + request_id + ".json"
    selection = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read(32769))
    if (selection.get("request_id") != request_id
            or selection.get("album_job_id") != album_job_id
            or not isinstance(selection.get("scenes"), list)
            or not selection["scenes"]
            or any(not isinstance(s, dict)
                   or s.get("scene_number") != i
                   or not isinstance(s.get("asset_id"), str)
                   or not re.fullmatch(r"[A-Za-z0-9_-]{10,64}", s["asset_id"])
                   or s.get("media_license") not in
                   {"owned_content", "cc0", "public_domain", "explicit_permission_granted"}
                   or s.get("rights_verified") is not True
                   for i, s in enumerate(selection["scenes"], 1))):
        raise ValueError("PRIVATE_MEDIA_INVALID: album selections not ready")
    return {"ready": True, "scene_count": len(selection["scenes"])}
