"""Load private verified research for an approved Telegram production request.

Never print research content or put it in GitHub artifacts.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path

from integrations.openmontage.private_request_store import get_request
from integrations.openmontage.r2_client import from_environment
from openmontage_fact_checker import verify_research_payload


def main():
    request_id = os.environ["REQUEST_ID"]
    storage = from_environment()
    request = get_request(storage, request_id=request_id)
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat or not hmac.compare_digest(
        request["owner_chat_sha256"], hashlib.sha256(chat.encode()).hexdigest()
    ):
        raise SystemExit("Unauthorized private render request")
    # Explicit research handoff; no synthetic news generation.
    key = f"openmontage/research/{request_id}.json"
    try:
        raw = storage.get_object(Key=key)["Body"].read()
    except Exception as exc:
        raise SystemExit("Verified research unavailable in private R2; render blocked") from exc
    research = json.loads(raw)
    checked = verify_research_payload(research)
    if checked.get("verified_item_count", 0) < 1:
        raise SystemExit("No verified research items; render blocked")
    path = Path("integrations/openmontage/.runtime/verified_research.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checked, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Private research loaded and checked; content withheld from logs")


if __name__ == "__main__":
    main()
