"""Review-gated R2 inbox -> existing guarded advisory task contract.

No arbitrary shell/code execution; lookup is restricted to a dated private R2 inbox.
The caller must explicitly review the selected task ID before running the separate
AI reviewer workflow. Not an automatic paid model dispatcher.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from scripts.cloud_ai_central import validate_task

PREFIX = "ai-central/v1/inbox/"
ID = re.compile(r"^[a-zA-Z0-9_-]{10,64}$")
DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
MAX_SCAN = 100

def select_draft(client, bucket, *, date, task_id):
    if not DATE.fullmatch(date) or dt.date.fromisoformat(date).isoformat() != date:
        raise ValueError("invalid inbox date")
    if not ID.fullmatch(task_id):
        raise ValueError("invalid inbox task ID")
    response = client.list_objects_v2(Bucket=bucket, Prefix=PREFIX + date + "/", MaxKeys=MAX_SCAN)
    if response.get("IsTruncated"):
        raise RuntimeError("Inbox exceeds safe bounded scan; choose narrower audited input")
    matches = []
    for obj in response.get("Contents", []):
        key = obj.get("Key", "")
        if not key.endswith(".json") or not key.startswith(PREFIX + date + "/"):
            continue
        raw = client.get_object(Bucket=bucket, Key=key)["Body"].read(10000)
        if len(raw) >= 10000:
            raise ValueError("oversized inbox draft")
        value = json.loads(raw)
        if value.get("id") == task_id:
            matches.append((key, value))
    if len(matches) != 1:
        raise ValueError("inbox task ID absent or ambiguous")
    key, draft = matches[0]
    if draft.get("schema") != "AI-INBOX-V1" or draft.get("status") != "DRAFT_REQUIRES_REVIEW" or draft.get("auto_dispatch") is not False:
        raise ValueError("draft not eligible for manual review")
    if draft.get("kind") != "message" or draft.get("channel") not in ("telegram", "web"):
        raise ValueError("only plain text drafts are eligible; file tasks need separate sandbox")
    message = draft.get("message")
    if not isinstance(message, str) or not 3 <= len(message) <= 2500:
        raise ValueError("invalid draft content")
    task = validate_task({
        "title": "Reviewed inbox task " + task_id[:32],
        "question": message,
        "evidence": "User-supplied question only. No external logs supplied. Require verifiable evidence before proposing any fix."
    })
    return {"r2_inbox_key": key, "inbox_id": task_id, "channel": draft["channel"], "task": task}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--output", default="reviewed-central-task.json")
    args = parser.parse_args()
    fields = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
    if not all(os.getenv(x) for x in fields):
        raise RuntimeError("R2 secrets unavailable")
    import boto3
    client = boto3.client("s3", endpoint_url="https://" + os.environ["R2_ACCOUNT_ID"] + ".r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    selected = select_draft(client, os.environ["R2_BUCKET_NAME"], date=args.date, task_id=args.id)
    # Public job logs carry only metadata; user question remains inside restricted job artifact.
    Path(args.output).write_text(json.dumps(selected["task"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "REVIEWED_DRAFT_EXPORTED", "inbox_id": selected["inbox_id"],
                      "channel": selected["channel"], "r2_source": selected["r2_inbox_key"],
                      "execution": "NOT_STARTED", "billing": "NONE"}))

if __name__ == "__main__":
    main()
