"""Shared R2 inbox schema for Telegram and dashboard. Never executes commands."""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from uuid import uuid4
SCHEMA="EDIRNE22-CONTROL-INBOX-V1"
MAX_TEXT=2500
def make_request(text, *, channel, source_id=None):
    if channel not in ("telegram","web"):raise ValueError("invalid channel")
    if not isinstance(text,str) or not text.strip() or len(text)>MAX_TEXT or any(ord(ch) < 32 for ch in text):
        raise ValueError("invalid message")
    if source_id is not None and not re.fullmatch(r"[0-9]{1,18}",str(source_id)):
        raise ValueError("invalid source id")
    request_id=str(uuid4())
    return {"schema":SCHEMA,"request_id":request_id,"channel":channel,
            "source_id":str(source_id) if source_id is not None else None,
            "created_at":datetime.now(timezone.utc).isoformat(),"status":"PENDING_REVIEW",
            "text":text.strip(),"approval":None}
def request_key(payload):
    if payload.get("schema")!=SCHEMA or payload.get("status")!="PENDING_REVIEW":raise ValueError("invalid request")
    return "ai-central/v1/inbox/"+payload["request_id"]+".json"
def save_telegram_message(text,update_id,*,client=None):
    """Called by existing authenticated single-chat Telegram router before it ACKs the update."""
    fields=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME")
    if not all(os.environ.get(k) for k in fields):
        raise RuntimeError("central Telegram R2 inbox not configured")
    data=make_request(text,channel="telegram",source_id=update_id)
    # Telegram retries should not generate a second request when the update is repeated.
    key="ai-central/v1/telegram-updates/"+str(update_id)+".json"
    if client is None:
        import boto3
        client=boto3.client("s3",region_name="auto",
          endpoint_url="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com",
          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    try:
        existing=client.get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=key)
        old=json.loads(existing["Body"].read(12000))
        if old.get("schema")==SCHEMA and old.get("source_id")==str(update_id):return old["request_id"]
        raise RuntimeError("existing Telegram update has unexpected schema")
    except Exception as exc:
        if not getattr(exc,"response",{}).get("Error",{}).get("Code") in ("404","NoSuchKey","NotFound"):
            raise
    client.put_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=key,
        Body=json.dumps(data,ensure_ascii=False).encode("utf-8"),ContentType="application/json")
    return data["request_id"]
