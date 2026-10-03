"""Read-only metadata check for an owner-authorized real Telegram album.

Does not download personal photos/video or write GitHub artifacts. This script
verifies remote R2 manifest + object HEAD metadata only, NOT actual byte hashes,
Telegram delivery, the owner's visual review, or the absence of unrelated posts.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import job_prefix


def verify(client, bucket, *, job_id, expected_count):
    if not re.fullmatch(r"tgalbum[a-f0-9]{32}", job_id):
        raise ValueError("Use the exact tgalbum... ID from the private bot receipt")
    if not isinstance(expected_count, int) or not 1 <= expected_count <= 100:
        raise ValueError("Expected album size must be between 1 and 100")
    index_key = "private/v1/telegram-album-index/" + job_id + ".json"
    record = json.loads(client.get_object(Bucket=bucket, Key=index_key)["Body"].read(4096))
    if record.get("job_id") != job_id or record.get("lane") != "private":
        raise RuntimeError("LIVE_INDEX_IDENTITY_OR_LANE_MISMATCH")
    timestamp = datetime.fromisoformat(record["created_at"])
    if timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc):
        raise RuntimeError("LIVE_INDEX_INVALID_TIMESTAMP")
    prefix = job_prefix("private", timestamp, job_id)
    key = prefix + "manifest.json"
    manifest = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read(200000))
    if (manifest.get("schema") != "MEDIA-JOB-MANIFEST-V1"
            or manifest.get("job_id") != job_id
            or manifest.get("lane") != "private"
            or manifest.get("prefix") != prefix
            or manifest.get("created_at") != record["created_at"]
            or manifest.get("status") != "INTAKE"
            or manifest.get("outputs") != []):
        raise RuntimeError("LIVE_MANIFEST_INVALID_OR_NONPRIVATE")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or len(assets) != expected_count:
        raise RuntimeError("LIVE_ASSET_COUNT_MISMATCH")
    seen = set()
    allowed = {"image/jpeg", "image/png", "video/mp4", "video/quicktime"}
    for item in assets:
        asset_id = item.get("asset_id")
        object_key = item.get("key")
        if (not isinstance(asset_id, str) or not re.fullmatch(r"file[a-f0-9]{32}", asset_id)
                or asset_id in seen
                or not isinstance(object_key, str)
                or not object_key.startswith(prefix + "originals/" + asset_id + "/")
                or item.get("mime") not in allowed
                or not isinstance(item.get("size"), int) or item["size"] < 1
                or not re.fullmatch(r"[a-f0-9]{64}", str(item.get("sha256", "")))):
            raise RuntimeError("LIVE_ASSET_METADATA_MISMATCH")
        seen.add(asset_id)
        metadata = client.head_object(Bucket=bucket, Key=object_key)
        if (metadata.get("ContentLength") != item["size"]
                or metadata.get("ContentType") != item["mime"]):
            raise RuntimeError("LIVE_ORIGINAL_HEAD_MISMATCH")
    quarantine = client.list_objects_v2(Bucket=bucket, Prefix=prefix + "quarantine/", MaxKeys=1)
    if quarantine.get("Contents"):
        raise RuntimeError("LIVE_UNREPLAYED_QUARANTINE")
    # No secrets, file names, album content, object keys or full chat IDs logged.
    print("REAL_TELEGRAM_R2_METADATA_PASS private=yes "
          "originals_present=" + str(expected_count)
          + " same_manifest=yes quarantine_empty=yes "
          "no_personal_download=yes byte_sha256_not_checked=yes")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    client, bucket = client_from_env()
    verify(client, bucket, job_id=args.job_id, expected_count=args.expected_count)


if __name__ == "__main__":
    main()
