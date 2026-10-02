"""Verify Cloudflare private R2 S3 If-Match CAS using isolated non-user objects.

This checks canonical job-store write semantics only, NEVER creates a real
Factory job, review intent, human approval or social publication.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from media_storage import R2Storage

PREFIX = "ai-central/v1/canonical-cas-smoke/"


def _code(exc):
    try:
        return str(exc.response["Error"]["Code"])
    except (AttributeError, KeyError, TypeError):
        return ""


def exercise_conditional_cas(client, bucket, key):
    if not key.startswith(PREFIX):
        raise ValueError("smoke only supports isolated non-canonical prefix")
    payload=json.dumps({"schema":"R2-CAS-ISOLATED-SMOKE","version":1}).encode()
    client.put_object(Bucket=bucket,Key=key,Body=payload,
                      ContentType="application/json",IfNoneMatch="*")
    original=client.get_object(Bucket=bucket,Key=key)
    etag=original["ETag"]
    if not etag or json.load(original["Body"])["version"]!=1:
        raise RuntimeError("smoke first write unreadable")
    def write(candidate):
        try:
            client.put_object(Bucket=bucket,Key=key,
                Body=json.dumps({"schema":"R2-CAS-ISOLATED-SMOKE",
                                 "version":candidate}).encode(),
                ContentType="application/json",IfMatch=etag)
            return "COMMITTED"
        except Exception as exc:
            if _code(exc) in ("PreconditionFailed","412","ConditionalRequestConflict","409"):
                return "STALE_BLOCKED"
            raise
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=sorted(pool.map(write,(2,3)))
    if outcomes!=["COMMITTED","STALE_BLOCKED"]:
        raise RuntimeError(f"private R2 IfMatch CAS contract failed: {outcomes}")
    fresh=client.get_object(Bucket=bucket,Key=key)
    try:
        saved=json.load(fresh["Body"])
        if saved["schema"]!="R2-CAS-ISOLATED-SMOKE" or saved["version"] not in (2,3):
            raise RuntimeError("unexpected isolated smoke persisted state")
        return saved["version"]
    finally:
        # Test object only; never delete media or a real Factory job.
        client.delete_object(Bucket=bucket,Key=key)


def run():
    if os.getenv("BLOCK8_PRIVATE_R2_CAS_SMOKE_APPROVED")!="true":
        raise RuntimeError("BLOCK8_REAL_R2_SMOKE_NOT_APPROVED")
    with tempfile.TemporaryDirectory(prefix="block8-cas-") as td:
        storage=R2Storage.from_env(cache_root=Path(td)/"cache")
        version=exercise_conditional_cas(storage.client,storage.bucket,
                                         PREFIX+str(uuid4())+".json")
        print("BLOCK8_PRIVATE_R2_IFMATCH_LIVE_PASS "+
              f"concurrent_winner=1 stale_writer_blocked=1 saved_version={version} "+
              "isolated_objects_cleaned=true real_human_actions=0 real_platform_requests=0")


if __name__=="__main__":
    run()
