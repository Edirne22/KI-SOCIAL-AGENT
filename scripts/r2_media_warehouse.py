"""Private/social R2 media key and manifest contract. No public URLs or cross-lane moves."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
import uuid

LANES = frozenset(("private", "social"))
SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{10,64}$")
MAX_ASSETS = 100

def lane_for_upload(*, explicit_social=False, contains_children=False):
    """Fail closed: children and unspecified uploads always stay private."""
    return "social" if explicit_social and not contains_children else "private"

def job_prefix(lane, created_at, job_id):
    if lane not in LANES or not SAFE_ID.fullmatch(job_id):
        raise ValueError("invalid lane or job ID")
    if created_at.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return f"{lane}/v1/{created_at.astimezone(timezone.utc):%Y/%m/%d}/{job_id}/"

def new_manifest(*, lane, title, created_at=None, job_id=None):
    created_at = created_at or datetime.now(timezone.utc)
    job_id = job_id or uuid.uuid4().hex
    prefix = job_prefix(lane, created_at, job_id)
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
        raise ValueError("invalid title")
    return {"schema":"MEDIA-JOB-MANIFEST-V1","job_id":job_id,"lane":lane,
            "display_title":title.strip(),"created_at":created_at.isoformat(),
            "status":"INTAKE","assets":[],"outputs":[],"prefix":prefix}

def append_asset(manifest, *, asset_id, filename, mime, payload, received_at=None):
    """Return new manifest and immutable object key; caller writes object before manifest."""
    prefix = job_prefix(manifest["lane"], datetime.fromisoformat(manifest["created_at"]), manifest["job_id"])
    if not SAFE_ID.fullmatch(asset_id) or not isinstance(payload, bytes) or not payload:
        raise ValueError("invalid asset")
    if len(manifest["assets"]) >= MAX_ASSETS or any(a["asset_id"] == asset_id for a in manifest["assets"]):
        raise ValueError("duplicate asset or asset limit")
    if mime not in {"image/jpeg","image/png","image/webp","video/mp4","video/quicktime"}:
        raise ValueError("unsupported media type")
    if not isinstance(filename,str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,120}",filename) or filename in {".",".."}:
        raise ValueError("unsafe filename")
    key = prefix + f"originals/{asset_id}/{filename}"
    asset = {"asset_id":asset_id,"original_filename":filename,"mime":mime,
             "size":len(payload),"sha256":sha256(payload).hexdigest(),
             "received_at":(received_at or datetime.now(timezone.utc)).isoformat(),"key":key}
    return {**manifest,"assets":[*manifest["assets"],asset]}, key

def store_original(client,bucket,manifest,*,asset_id,filename,mime,payload):
    """R2 first, manifest last. Never overwrite originals or acknowledge failed writes."""
    updated,key=append_asset(manifest,asset_id=asset_id,filename=filename,mime=mime,payload=payload)
    client.put_object(Bucket=bucket,Key=key,Body=payload,ContentType=mime,IfNoneMatch="*")
    # Manifest updates are compare-and-swap: never silently lose another upload.\n    manifest_key=manifest["prefix"]+"manifest.json"\n    try:\n        existing=client.get_object(Bucket=bucket,Key=manifest_key)\n    except Exception as exc:\n        code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))\n        if code not in ("404","NoSuchKey","NotFound"):\n            raise\n        existing=None\n    if existing is None:\n        if manifest["assets"]:\n            raise RuntimeError("manifest missing after previous upload; recovery required")\n        condition={"IfNoneMatch":"*"}\n    else:\n        previous=json.loads(existing["Body"].read())\n        if previous != manifest:\n            raise RuntimeError("manifest changed concurrently; reload before retry")\n        etag=existing.get("ETag")\n        if not etag:\n            raise RuntimeError("manifest ETag missing; unsafe update blocked")\n        condition={"IfMatch":etag}\n    client.put_object(Bucket=bucket,Key=manifest_key,\n                      Body=json.dumps(updated,ensure_ascii=False).encode("utf-8"),\n                      ContentType="application/json",**condition)
    return updated
