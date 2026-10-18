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
            or any(s.get("rights_verified") is not True
                   for s in selection["scenes"] if isinstance(s, dict))
            or any(not isinstance(s, dict) for s in selection["scenes"])):
        raise ValueError("PRIVATE_MEDIA_INVALID: album selections not ready")
    return {"ready": True, "scene_count": len(selection["scenes"])}
