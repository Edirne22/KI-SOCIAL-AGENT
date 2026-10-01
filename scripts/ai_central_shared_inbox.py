"""Shared private R2 inbox adapter for the existing single Telegram poller.

Only explicit /zentrale commands. No publishing, model calls or workflow dispatch.
Do not log user messages or R2 credentials. Telegram update id provides idempotency.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re

PREFIX = "ai-central/v1/inbox/"
MAX_MESSAGE = 2500
_BLOCKED = re.compile(r"(?i)(?:authorization\s*:\s*bearer|api[_-]?key\s*[=:]|secret\s*[=:]|password\s*[=:])\s*\S+")

def parse_command(text: str):
    if not isinstance(text,str):
        return None
    normalized=text.strip()
    match=re.fullmatch(r"/?zentrale\s+(status|hilfe|auftrag(?:\s+(.+))?)",normalized,re.I|re.S)
    if not match:
        return None
    name=match.group(1).split()[0].lower()
    if name=="auftrag":
        message=(match.group(2) or "").strip()
        if not 3<=len(message)<=MAX_MESSAGE or _BLOCKED.search(message) or any(ord(c)<32 and c not in "\n\t" for c in message):
            raise ValueError("Bitte einen Auftrag mit 3 bis 2500 Zeichen und ohne Zugangsdaten eingeben.")
        return "auftrag",message
    return name,None

def client_from_env():
    names=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME")
    if not all(os.environ.get(x) for x in names):
        raise RuntimeError("R2-Zugang der KI-Zentrale noch nicht konfiguriert")
    import boto3
    client=boto3.client("s3",endpoint_url="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
    return client,os.environ["R2_BUCKET_NAME"]

def submit(client,bucket,*,update_id:int,chat_id:str,message:str,now=None):
    if not isinstance(update_id,int) or update_id<1 or not chat_id:
        raise ValueError("invalid Telegram update")
    if not 3<=len(message)<=MAX_MESSAGE or _BLOCKED.search(message):
        raise ValueError("invalid message")
    now=now or datetime.now(timezone.utc)
    # Stable idempotency key: retries of the same update cannot create duplicate tasks.
    digest=sha256(f"{chat_id}:{update_id}".encode()).hexdigest()[:24]
    key=PREFIX+now.strftime("%Y-%m-%d")+"/telegram-"+digest+".json"
    try:
        found=client.head_object(Bucket=bucket,Key=key)
        if found:return {"id":digest,"status":"DRAFT_REQUIRES_REVIEW","duplicate":True}
    except Exception as exc:
        # S3 HeadObject reports absent keys via ClientError(404/NoSuchKey).
        code=str(getattr(exc, 'response', {}).get('Error', {}).get('Code',''))
        if code not in {'404','NoSuchKey','NotFound'}:
            raise
    task={"schema":"AI-INBOX-V1","id":digest,"created_at":now.isoformat(),
          "channel":"telegram","kind":"message","message":message,
          "status":"DRAFT_REQUIRES_REVIEW","auto_dispatch":False}
    client.put_object(Bucket=bucket,Key=key,Body=json.dumps(task,ensure_ascii=False).encode(),
          ContentType="application/json")
    return {"id":digest,"status":task["status"],"duplicate":False}

def recent(client,bucket,limit=6):
    # Same schema/prefix as the Worker; lightweight Telegram snapshot.
    found=client.list_objects_v2(Bucket=bucket,Prefix=PREFIX,MaxKeys=100)
    objects=sorted((x["Key"] for x in found.get("Contents",[]) if x["Key"].endswith(".json")),reverse=True)[:limit]
    result=[]
    for key in objects:
        item=json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(8000))
        result.append({k:item.get(k) for k in ("id","created_at","channel","kind","status","message")})
    return result

def handle(text,update_id,chat_id,*,client=None,bucket=None):
    parsed=parse_command(text)
    if parsed is None:return None
    op,message=parsed
    if op=="hilfe":
        return "KI-Zentrale: /zentrale status oder /zentrale auftrag DEIN TEXT. Erst Entwurf, keine automatische Ausführung."
    if client is None:
        client,bucket=client_from_env()
    if not bucket:raise ValueError("R2 bucket missing")
    if op=="status":
        items=recent(client,bucket)
        if not items:return "KI-Zentrale: noch keine gemeinsamen Web-/Telegram-Entwürfe."
        return "KI-Zentrale · letzte Entwürfe:\n"+"\n".join(
            f"{x['channel']}: {str(x.get('message') or '[Datei]')[:65]} · {x['status']}" for x in items)
    out=submit(client,bucket,update_id=update_id,chat_id=chat_id,message=message)
    return ("Bereits gespeichert" if out["duplicate"] else "Entwurf gespeichert")+f" · {out['id']}. Im Dashboard sichtbar; noch kein KI-Start."
