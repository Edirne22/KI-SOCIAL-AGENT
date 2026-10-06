"""Bounded production watcher for the exact private Dünya Level 12 task.

Reads only PRIVATE-VIDEO-STATUS-V1 metadata and the final private preview manifest.
Never reads private media or the private prompt. On FAILED/STALLED it persists one
bounded incident for Agent 21; it never restarts the job itself.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from scripts.ai_central_shared_inbox import client_from_env
from scripts.production_machine_watchdog import inspect, private_video_status_sample

TASK_ID = "f6f50c9f4c2690e4eb1fe978"
STATUS_KEY = f"ai-central/v1/private-video/{TASK_ID}/status.json"
PREVIEW_KEY = f"ai-central/v1/private-video/{TASK_ID}/preview.json"
INCIDENT_PREFIX = "ai-central/v1/maintenance/incidents/"
TERMINAL = {"COMPLETED", "FAILED"}


def _code(exc):
    return str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))


def load_status(client, bucket: str) -> dict:
    raw = client.get_object(Bucket=bucket, Key=STATUS_KEY)["Body"].read(12000)
    value = json.loads(raw)
    if value.get("schema") != "PRIVATE-VIDEO-STATUS-V1" or value.get("task_id") != TASK_ID:
        raise RuntimeError("DUENYA_WATCH_STATUS_INVALID")
    if value.get("status") not in {"ACCEPTED", "RUNNING", "COMPLETED", "FAILED"}:
        raise RuntimeError("DUENYA_WATCH_STATUS_VALUE_INVALID")
    return value


def verify_preview(client, bucket: str) -> dict:
    raw = client.get_object(Bucket=bucket, Key=PREVIEW_KEY)["Body"].read(12000)
    value = json.loads(raw)
    required = {"schema", "task_id", "state", "r2_key", "sha256", "private", "publishable"}
    if set(value) != required:
        raise RuntimeError("DUENYA_PREVIEW_SCHEMA_INVALID")
    if (
        value["schema"] != "PRIVATE-VIDEO-PREVIEW-V1"
        or value["task_id"] != TASK_ID
        or value["state"] != "READY_FOR_HUMAN"
        or value["private"] is not True
        or value["publishable"] is not False
        or not isinstance(value["r2_key"], str)
        or not value["r2_key"].startswith("private/")
        or not isinstance(value["sha256"], str)
        or len(value["sha256"]) != 64
    ):
        raise RuntimeError("DUENYA_PREVIEW_CONTRACT_INVALID")
    return {
        "state": value["state"],
        "r2_key": value["r2_key"],
        "sha256_prefix": value["sha256"][:12],
        "private": True,
        "publishable": False,
    }


def persist_incident(client, bucket: str, incident: dict, status: dict) -> str:
    allowed = {
        "schema": "MACHINE-WATCHDOG-INCIDENT-V1",
        "incident_id": incident["incident_id"],
        "job_id": incident["job_id"],
        "stage_id": incident["stage_id"],
        "machine": incident["machine"],
        "checkpoint": incident["checkpoint"],
        "last_progress": incident["last_progress"],
        "last_heartbeat_at": incident["last_heartbeat_at"],
        "reason": incident["reason"],
        "route_to": "agent21",
        "requested_action": "DIAGNOSE_ONLY",
        "error_code": str(status.get("error_code") or "")[:80],
        "detail": str(status.get("detail") or "")[:240],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    key = INCIDENT_PREFIX + allowed["incident_id"] + ".json"
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(allowed, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
        CacheControl="private, no-store",
        IfNoneMatch="*",
    )
    return key


def watch(
    client,
    bucket: str,
    *,
    sleeper=time.sleep,
    now_fn=lambda: datetime.now(timezone.utc),
    max_checks: int = 80,
    interval_seconds: int = 15,
    stall_after_seconds: int = 75,
) -> dict:
    if max_checks < 1 or interval_seconds < 0 or stall_after_seconds < 45:
        raise ValueError("DUENYA_WATCH_BOUNDS_INVALID")
    last_stamp = None
    for n in range(max_checks):
        status = load_status(client, bucket)
        sample = private_video_status_sample(status, now=now_fn(), stall_after_seconds=stall_after_seconds)
        decision = inspect(sample)
        state = sample["status"]
        stamp = status.get("updated_at")
        if stamp != last_stamp:
            print("DUENYA_WATCH_HEARTBEAT status="+state+" stage="+sample["stage_id"])
            last_stamp = stamp
        if state == "COMPLETED":
            preview = verify_preview(client, bucket)
            print("DUENYA_WATCH_COMPLETED preview=READY_FOR_HUMAN private=yes published=no sha256_prefix="+preview["sha256_prefix"])
            return {"status": "COMPLETED", "preview": preview}
        if state in {"FAILED", "STALLED"}:
            if decision.get("route_to") != "agent21":
                raise RuntimeError("DUENYA_WATCH_AGENT21_ROUTE_MISSING")
            try:
                key = persist_incident(client, bucket, decision, status)
            except Exception as exc:
                if _code(exc) not in {"PreconditionFailed", "412", "ConditionalRequestConflict", "409"}:
                    raise
                key = INCIDENT_PREFIX + decision["incident_id"] + ".json"
            print("DUENYA_WATCH_AGENT21_INCIDENT status="+state+" stage="+sample["stage_id"]+" incident="+decision["incident_id"])
            return {
                "status": state,
                "stage": sample["stage_id"],
                "incident_id": decision["incident_id"],
                "incident_key": key,
                "error_code": str(status.get("error_code") or "")[:80],
            }
        if n + 1 < max_checks:
            sleeper(interval_seconds)
    raise RuntimeError("DUENYA_WATCH_BOUNDED_TIMEOUT")


def main() -> int:
    client, bucket = client_from_env()
    result = watch(client, bucket)
    if result["status"] == "COMPLETED":
        return 0
    raise RuntimeError(
        "DUENYA_WATCH_NEEDS_AGENT21:"
        + result["status"] + ":"
        + result["stage"] + ":"
        + result["incident_id"] + ":"
        + result["error_code"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
