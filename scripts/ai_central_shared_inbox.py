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
import requests

PREFIX = "ai-central/v1/inbox/"
MAX_MESSAGE = 2500
_BLOCKED = re.compile(r"(?i)(?:authorization\s*:\s*bearer|api[_-]?key\s*[=:]|secret\s*[=:]|password\s*[=:])\s*\S+")

def parse_command(text: str):
    if not isinstance(text,str):
        return None
    normalized=text.strip()
    match=re.fullmatch(r"/?zentrale\s+(status|hilfe|starten(?:\s+([a-zA-Z0-9_-]{10,64}))?|auftrag(?:\s+(.+))?)",normalized,re.I|re.S)
    if not match:
        return None
    name=match.group(1).split()[0].lower()
    if name=="starten":
        ident=match.group(2)
        if not ident:raise ValueError("Bitte /zentrale starten <Auftrags-ID> eingeben.")
        return "starten",ident
    if name=="auftrag":
        message=(match.group(3) or "").strip()
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

def start_reviewed(client,bucket,task_id,token,post=requests.post):
    """Authorized existing Telegram chat explicitly starts ONE $0 reviewed workflow."""
    if not re.fullmatch(r"[a-zA-Z0-9_-]{10,64}",task_id):
        raise ValueError("Ungültige Auftrags-ID.")
    if not token:
        raise RuntimeError("GitHub-Startberechtigung noch nicht eingerichtet.")
    objects=client.list_objects_v2(Bucket=bucket,Prefix=PREFIX,MaxKeys=100)
    if objects.get("IsTruncated"):
        raise RuntimeError("Zu viele Entwürfe; bitte Dashboard nutzen.")
    found=[]
    for entry in objects.get("Contents",[]):
        key=entry.get("Key","")
        if not key.endswith(".json"):
            continue
        value=json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(10000))
        if value.get("id")==task_id:
            found.append((key,value))
    if len(found)!=1:
        raise ValueError("Auftrags-ID nicht gefunden oder doppelt vorhanden.")
    key,entry=found[0]
    if (entry.get("schema")!="AI-INBOX-V1" or entry.get("kind")!="message"
        or entry.get("status")!="DRAFT_REQUIRES_REVIEW" or entry.get("auto_dispatch") is not False):
        raise ValueError("Dieser Auftrag kann nicht gestartet werden.")
    day=str(entry.get("created_at",""))[:10]
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",day):
        raise ValueError("Auftragsdatum ungültig.")
    queued={**entry,"status":"QUEUED_FREE_REVIEW",
        "approved_at":datetime.now(timezone.utc).isoformat(),
        "dispatch_target":"ai-central-inbox-agent.yml","inference_scope":"openrouter/free"}
    client.put_object(Bucket=bucket,Key=key,Body=json.dumps(queued,ensure_ascii=False).encode(),
        ContentType="application/json")
    try:
        response=post("https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/workflows/ai-central-inbox-agent.yml/dispatches",
            headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
                "X-GitHub-Api-Version":"2022-11-28"},
            json={"ref":"main","inputs":{"inbox_date":day,"inbox_id":task_id}},timeout=20)
    except requests.RequestException:
        client.put_object(Bucket=bucket,Key=key,Body=json.dumps(entry,ensure_ascii=False).encode(),ContentType="application/json")
        raise RuntimeError("GitHub momentan nicht erreichbar; Entwurf beibehalten.")
    if response.status_code!=204:
        client.put_object(Bucket=bucket,Key=key,Body=json.dumps(entry,ensure_ascii=False).encode(),ContentType="application/json")
        raise RuntimeError("GitHub hat den Start nicht bestätigt; Entwurf beibehalten.")
    return "Auftrag "+task_id+" von GitHub angenommen. Das ist noch kein fertiges Ergebnis. Bericht später im Dashboard prüfen."

def handle(text,update_id,chat_id,*,client=None,bucket=None):
    parsed=parse_command(text)
    if parsed is None:return None
    op,message=parsed
    if op=="hilfe":
        return "KI-Zentrale: /zentrale auftrag TEXT · /zentrale status · /zentrale starten AUFTRAGS-ID. keine automatische Ausführung ohne expliziten Start; kostenlose Modellroute."
    if client is None:
        client,bucket=client_from_env()
    if not bucket:raise ValueError("R2 bucket missing")
    if op=="starten":
        return start_reviewed(client,bucket,message,os.environ.get("GITHUB_TOKEN",""))
    if op=="status":
        items=recent(client,bucket)
        if not items:return "KI-Zentrale: noch keine gemeinsamen Web-/Telegram-Entwürfe."
        return "KI-Zentrale · letzte Entwürfe:\n"+"\n".join(
            f"{x['channel']}: {str(x.get('message') or '[Datei]')[:65]} · {x['status']} · ID: {x['id']}" for x in items)
    out=submit(client,bucket,update_id=update_id,chat_id=chat_id,message=message)
    return ("Bereits gespeichert" if out["duplicate"] else "Entwurf gespeichert")+f" · {out['id']}. Im Dashboard sichtbar; noch kein KI-Start."
