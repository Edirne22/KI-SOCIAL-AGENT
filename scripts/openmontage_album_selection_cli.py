"""Owner-only CLI for explicit private OpenMontage album scene selection."""
import argparse
import json
import os
from pathlib import Path

from scripts.ai_central_shared_inbox import client_from_env
from scripts.openmontage_store_album_selection import store_album_selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--album-job-id", required=True)
    parser.add_argument("--selections", required=True, type=Path)
    args = parser.parse_args()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat:
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: Telegram owner not configured")
    with args.selections.open("rb") as f:
        payload = f.read(32769)
    if len(payload) > 32768:
        raise ValueError("PRIVATE_MEDIA_INVALID: selection exceeds 32 KiB")
    selections = json.loads(payload)
    client, bucket = client_from_env()
    result = store_album_selection(
        client, bucket, request_id=args.request_id,
        album_job_id=args.album_job_id, owner_chat=chat,
        authorized_chat=chat, selections=selections)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
