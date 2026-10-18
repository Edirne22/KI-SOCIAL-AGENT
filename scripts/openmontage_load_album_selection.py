"""Load an explicit private R2 album selection for one Telegram render request."""
import hashlib
import hmac
import json
import os
from pathlib import Path

from integrations.openmontage.private_request_store import get_request
from integrations.openmontage.r2_client import from_environment


def main():
    request_id = os.environ["REQUEST_ID"]
    storage = from_environment()
    request = get_request(storage, request_id=request_id)
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat or not hmac.compare_digest(
            request["owner_chat_sha256"], hashlib.sha256(chat.encode()).hexdigest()):
        raise SystemExit("Unauthorized private album selection")
    key = f"openmontage/album-selections/{request_id}.json"
    raw = storage.get_object(Key=key)["Body"].read(32769)
    if len(raw) > 32768:
        raise ValueError("PRIVATE_MEDIA_INVALID: oversized album selection")
    selection = json.loads(raw)
    if (not isinstance(selection, dict)
            or selection.get("request_id") != request_id
            or selection.get("album_job_id") != os.environ.get("ALBUM_JOB_ID")
            or not isinstance(selection.get("scenes"), list)
            or not selection["scenes"]):
        raise ValueError("PRIVATE_MEDIA_INVALID: explicit album selection missing or mismatched")
    dest = Path("integrations/openmontage/.runtime/album_selection.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"scenes": selection["scenes"]}), encoding="utf-8")
    print("Owner album selections loaded privately; no media URLs exposed")


if __name__ == "__main__":
    main()
