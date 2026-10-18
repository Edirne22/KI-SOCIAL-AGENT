"""Read-only private album readiness check for operators."""
import argparse
import json
import os

from scripts.ai_central_shared_inbox import client_from_env
from scripts.openmontage_album_preflight import preflight_album


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--album-job-id", required=True)
    args = parser.parse_args()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat:
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: owner not configured")
    client, bucket = client_from_env()
    result = preflight_album(
        client, bucket, request_id=args.request_id,
        album_job_id=args.album_job_id, owner_chat=chat, authorized_chat=chat)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
