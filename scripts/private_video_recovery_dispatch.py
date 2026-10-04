"""One-time safe recovery for an explicitly approved private video task misrouted to generic AI review.

Reads only private R2 inbox metadata, never logs the private message, and only
reroutes one recent task that already carries the user's approval timestamp.
Rendering stays in the protected media container; no social publisher is reachable.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import json
import os
import requests
from scripts.ai_central_shared_inbox import PREFIX, _is_private_video_request, client_from_env

MAX_SCAN = 100
MAX_AGE = timedelta(hours=24)

def _code(exc):
    return str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))

def main() -> int:
    client,bucket=client_from_env()
    page=client.list_objects_v2(Bucket=bucket,Prefix=PREFIX,MaxKeys=MAX_SCAN)
    if page.get("IsTruncated"):
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_SCAN_TRUNCATED")
    now=datetime.now(timezone.utc)
    candidates=[]
    for item in page.get("Contents",[]):
        key=item.get("Key","")
        if not key.endswith(".json"):
            continue
        obj=client.get_object(Bucket=bucket,Key=key)
        doc=json.loads(obj["Body"].read(12000))
        try:
            created=datetime.fromisoformat(str(doc.get("created_at","")))
        except ValueError:
            continue
        if created.tzinfo is None or now-created > MAX_AGE or created > now+timedelta(minutes=5):
            continue
        if (doc.get("schema")=="AI-INBOX-V1" and doc.get("kind")=="message"
            and doc.get("status")=="QUEUED_FREE_REVIEW"
            and doc.get("dispatch_target")=="ai-central-inbox-agent.yml"
            and doc.get("auto_dispatch") is False and doc.get("approved_at")
            and _is_private_video_request(doc.get("message",""))):
            candidates.append((key,doc,obj.get("ETag")))
    if not candidates:
        print("PRIVATE_VIDEO_RECOVERY_NONE")
        return 0
    if len(candidates)!=1:
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_AMBIGUOUS")
    key,doc,etag=candidates[0]
    if not isinstance(etag,str) or not etag:
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_ETAG_MISSING")
    endpoint=os.environ.get("PRIVATE_MEDIA_RUNTIME_URL","").strip()
    token=os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN","").strip()
    if not endpoint or not token:
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_RUNTIME_UNCONFIGURED")
    claimed={**doc,"status":"QUEUED_PRIVATE_VIDEO","dispatch_target":"private-media-container",
             "inference_scope":"none-private-ffmpeg"}
    result=client.put_object(Bucket=bucket,Key=key,
        Body=json.dumps(claimed,ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",IfMatch=etag)
    if not result.get("ETag"):
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_CLAIM_UNCERTAIN")
    try:
        response=requests.post(endpoint,headers={"Authorization":"Bearer "+token},
                               json={"task_id":doc["id"]},timeout=25)
    except requests.RequestException as exc:
        raise RuntimeError("PRIVATE_VIDEO_RECOVERY_DISPATCH_UNCERTAIN") from exc
    if response.status_code not in (200,202):
        raise RuntimeError(f"PRIVATE_VIDEO_RECOVERY_RUNTIME_HTTP_{response.status_code}")
    print("PRIVATE_VIDEO_RECOVERY_ACCEPTED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
