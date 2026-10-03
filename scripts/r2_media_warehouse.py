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
    try:
        client.put_object(Bucket=bucket,Key=key,Body=payload,ContentType=mime,IfNoneMatch="*")
    except Exception as exc:
        # A previous attempt may have stored the immutable original before its
        # manifest write failed. Never overwrite it: verify before recovery.
        code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
        if code not in ("PreconditionFailed","412","ConditionalRequestConflict","409"):
            raise
        existing=client.get_object(Bucket=bucket,Key=key)["Body"].read()
        if sha256(existing).digest()!=sha256(payload).digest() or len(existing)!=len(payload):
            raise RuntimeError("immutable original collision or corrupt prior write") from exc

    # Verify the immutable object before making it visible in the manifest.
    stored=client.get_object(Bucket=bucket,Key=key)["Body"].read()
    if sha256(stored).digest()!=sha256(payload).digest():
        raise RuntimeError("R2 original readback mismatch; manifest not committed")
    # Manifest updates are compare-and-swap: never silently lose another upload.
    manifest_key=manifest["prefix"]+"manifest.json"
    try:
        existing=client.get_object(Bucket=bucket,Key=manifest_key)
    except Exception as exc:
        code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
        if code not in ("404","NoSuchKey","NotFound"):
            raise
        existing=None
    if existing is None:
        if manifest["assets"]:
            raise RuntimeError("manifest missing after previous upload; recovery required")
        condition={"IfNoneMatch":"*"}
    else:
        previous=json.loads(existing["Body"].read())
        if previous != manifest:
            raise RuntimeError("manifest changed concurrently; reload before retry")
        etag=existing.get("ETag")
        if not etag:
            raise RuntimeError("manifest ETag missing; unsafe update blocked")
        condition={"IfMatch":etag}
    client.put_object(Bucket=bucket,Key=manifest_key,
                      Body=json.dumps(updated,ensure_ascii=False).encode("utf-8"),
                      ContentType="application/json",**condition)
    return updated
