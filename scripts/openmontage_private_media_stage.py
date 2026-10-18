"""B72B: stage explicitly selected private R2 originals for local rendering.

No Telegram download, publishing, or implicit rights grant happens here.
The caller owns the temporary directory and must remove it after rendering.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

MAX_ASSET_BYTES = 19 * 1024 * 1024
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "video/mp4": ".mp4"}
ASSET_ID = re.compile(r"^[A-Za-z0-9_-]{10,64}$")


def stage_private_scenes(client, bucket: str, manifest: dict, selections: list[dict],
                         destination: Path) -> dict:
    """Stage owner-selected assets and return a B72A scene configuration.

    selections: [{scene_number, asset_id, media_license, rights_verified}].
    A caller must separately establish ownership/authorization of the manifest.
    """
    if (not isinstance(manifest, dict) or manifest.get("schema") != "MEDIA-JOB-MANIFEST-V1"
            or manifest.get("lane") != "private" or not isinstance(selections, list)
            or not selections or not isinstance(bucket, str) or not bucket):
        raise ValueError("PRIVATE_MEDIA_INVALID: private manifest or selections missing")
    prefix = manifest.get("prefix")
    if (not isinstance(prefix, str) or not re.fullmatch(
            r"private/v1/\d{4}/\d{2}/\d{2}/[A-Za-z0-9_-]{10,64}/", prefix)
            or prefix.split("/")[-2] != manifest.get("job_id")):
        raise ValueError("PRIVATE_MEDIA_INVALID: unsafe manifest prefix")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or len(assets) > 100:
        raise ValueError("PRIVATE_MEDIA_INVALID: invalid assets")
    indexed = {a.get("asset_id"): a for a in assets if isinstance(a, dict)}
    if len(indexed) != len(assets):
        raise ValueError("PRIVATE_MEDIA_INVALID: duplicate asset identity")
    accepted = []
    for index, selection in enumerate(selections, 1):
        if not isinstance(selection, dict) or selection.get("scene_number") != index:
            raise ValueError("PRIVATE_MEDIA_INVALID: scene order mismatch")
        aid = selection.get("asset_id")
        if not isinstance(aid, str) or not ASSET_ID.fullmatch(aid) or aid not in indexed:
            raise ValueError("PRIVATE_MEDIA_INVALID: unknown asset")
        if (selection.get("rights_verified") is not True or
                selection.get("media_license") not in
                {"owned_content", "cc0", "public_domain", "explicit_permission_granted"}):
            raise ValueError("PRIVATE_MEDIA_INVALID: explicit media approval required")
        asset = indexed[aid]
        mime = asset.get("mime")
        key = asset.get("key")
        size = asset.get("size")
        digest = asset.get("sha256")
        if (mime not in EXTENSIONS or not isinstance(key, str)
                or not key.startswith(prefix + "originals/" + aid + "/")
                or not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", key.rsplit("/", 1)[-1])
                or not isinstance(size, int) or isinstance(size, bool)
                or not 0 < size <= MAX_ASSET_BYTES
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("PRIVATE_MEDIA_INVALID: unsupported or unsafe original")
        accepted.append((selection, asset))
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and any(destination.iterdir())):
        raise ValueError("PRIVATE_MEDIA_INVALID: staging directory must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    scenes = []
    try:
        for index, (selection, asset) in enumerate(accepted, 1):
            stream = client.get_object(Bucket=bucket, Key=asset["key"])["Body"]
            payload = stream.read(MAX_ASSET_BYTES + 1)
            if (len(payload) != asset["size"]
                    or sha256(payload).hexdigest() != asset["sha256"]):
                raise ValueError("PRIVATE_MEDIA_INVALID: original size/hash mismatch")
            name = f"scene_{index:03d}" + EXTENSIONS[asset["mime"]]
            (destination / name).write_bytes(payload)
            scenes.append({"scene_number": index, "local_path": name,
                           "media_license": selection["media_license"],
                           "rights_verified": True})
    except Exception:
        for scene in scenes:
            (destination / scene["local_path"]).unlink(missing_ok=True)
        raise
    return {"all_rights_verified": True, "scenes": scenes}
