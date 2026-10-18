"""Load a private Telegram film request on a GitHub runner without logging prompt."""
from __future__ import annotations

import json
import os
from pathlib import Path

from integrations.openmontage.private_request_store import get_request


def main():
    request_id = os.environ["REQUEST_ID"]
    if not request_id:
        raise SystemExit("Telegram request ID required for private request handoff")
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
    if any(not os.environ.get(k) for k in required):
        raise SystemExit("R2 request transport not configured")
    import boto3
    client = boto3.client(
        "s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    storage = client  # Bucket supplied through a private-scoped adapter.
    class BucketClient:
        def get_object(self, *, Key):
            return storage.get_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=Key)
    request = get_request(BucketClient(), request_id=request_id)
    # Do not write the prompt into a GitHub artifact, step output or log.
    result = {"request_id": request["request_id"], "status": "REQUEST_VALIDATED",
              "prompt_characters": len(request["prompt"])}
    output = Path("integrations/openmontage/.runtime/request_status.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Private OpenMontage request validated; no render dispatched.")


if __name__ == "__main__":
    main()
