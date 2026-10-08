"""Agent 11 executable recovery adapter for a validated Agent-21 handoff.

The handoff contains no URL, token or shell command. Runtime origin is fixed here.
Only the existing private-media-container and RESUME action are executable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.ai_central_shared_inbox import client_from_env
from scripts.production_recovery_contract import (
    healthy_after_restart,
    recovery_decision,
    validate_handoff,
)

RUNTIME_ORIGIN = "https://edirne22-private-asr.butupeli.workers.dev"
STATUS_SCHEMA = "PRIVATE-VIDEO-STATUS-V1"
RECOVERY_SCHEMA = "PRODUCTION-RECOVERY-R2-V1"
DEFAULT_PRODUCTION_REVISION = "v4"
RUNTIME_REVISION = "duenya-creative-chain-v3"


def _http_json(method: str, path: str, token: str, payload: dict | None = None) -> tuple[int, dict]:
    allowed = {
        ("POST", "/admin/container-restart"),
        ("GET", "/health"),
        ("POST", "/admin/container-restart"),
        ("POST", "/private-video/jobs"),
    }
    if (method, path) not in allowed:
        raise ValueError("RECOVERY_HTTP_PATH_NOT_ALLOWED")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        # Explicit service identity: the default Python UA receives upstream 403.
        "User-Agent": "Edirne22-Private-Video-Recovery/1.0",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if method == "POST" and path == "/admin/container-restart":
        headers["X-Edirne22-Recovery-Action"] = "resume_duenya_v4"
    request = Request(RUNTIME_ORIGIN + path, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=35) as response:
            raw = response.read(16384).decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read(16384).decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"error": "non_json"}
        return exc.code, data
    except URLError as exc:
        raise RuntimeError("RECOVERY_RUNTIME_UNREACHABLE") from exc


def _load_status(client, bucket: str, job_id: str, production_revision: str) -> dict:
    key = f"ai-central/v1/private-video/{job_id}/revisions/{production_revision}/status.json"
    raw = client.get_object(Bucket=bucket, Key=key)["Body"].read(16384)
    value = json.loads(raw)
    if value.get("schema") != STATUS_SCHEMA or value.get("task_id") != job_id:
        raise RuntimeError("RECOVERY_STATUS_CONTRACT_INVALID")
    if (value.get("production_revision") != production_revision
        or value.get("runtime_revision") != RUNTIME_REVISION):
        raise RuntimeError("RECOVERY_STATUS_REVISION_MISMATCH")
    stage = value.get("stage")
    status = value.get("status")
    updated_at = value.get("updated_at")
    if not isinstance(stage, str) or not stage:
        raise RuntimeError("RECOVERY_STATUS_STAGE_MISSING")
    if status not in {"ACCEPTED", "RUNNING", "COMPLETED", "FAILED"}:
        raise RuntimeError("RECOVERY_STATUS_VALUE_INVALID")
    if not isinstance(updated_at, str) or not updated_at:
        raise RuntimeError("RECOVERY_STATUS_HEARTBEAT_MISSING")
    return {
        "job_id": job_id,
        "stage_id": stage,
        "checkpoint": stage,
        "status": status,
        "updated_at": updated_at,
    }


def _persist_recovery(client, bucket: str, handoff: dict, result: dict) -> None:
    key = f"ai-central/v1/private-video/{handoff['job_id']}/recovery/{handoff['repair_id']}.json"
    record = {
        "schema": RECOVERY_SCHEMA,
        "at": datetime.now(timezone.utc).isoformat(),
        "repair_id": handoff["repair_id"],
        "job_id": handoff["job_id"],
        "production_revision": result.get("production_revision"),
        "stage_id": handoff["stage_id"],
        "machine": handoff["machine"],
        "requested_action": handoff["requested_action"],
        "decision": result["decision"],
        "reason": result["reason"],
        "recovered": result.get("recovered") is True,
    }
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(record, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
        CacheControl="private, no-store",
        IfNoneMatch="*",
    )


def execute_recovery(
    client,
    bucket: str,
    handoff: dict,
    token: str,
    *,
    http=_http_json,
    sleeper=time.sleep,
    max_health_attempts: int = 8,
    max_heartbeat_attempts: int = 8,
    production_revision: str = DEFAULT_PRODUCTION_REVISION,
) -> dict:
    h = validate_handoff(handoff)
    if production_revision not in {"v3", "v4"}:
        raise ValueError("RECOVERY_PRODUCTION_REVISION_INVALID")
    if h["machine"] != "private-media-container":
        raise ValueError("RECOVERY_MACHINE_NOT_EXECUTABLE")
    if h["requested_action"] != "RESUME":
        raise ValueError("RECOVERY_ACTION_NOT_EXECUTABLE")
    if not token:
        raise RuntimeError("RECOVERY_RUNTIME_TOKEN_MISSING")

    current = _load_status(client, bucket, h["job_id"], production_revision)
    decision = recovery_decision(h, {k: current[k] for k in ("job_id", "stage_id", "checkpoint", "status")})
    if decision["decision"] in {"NO_RESTART", "OBSERVE_ONLY"}:
        result = {**decision, "recovered": False, "production_revision": production_revision}
        _persist_recovery(client, bucket, h, result)
        return result
    if decision["decision"] != "RESUME":
        raise RuntimeError("RECOVERY_DECISION_NOT_EXECUTABLE")

    # The already-proven authenticated admin path performs one container restart.
    # A fixed header selects only the pinned Dünya V4 resume; public private-video
    # route paths and JSON-body commands returned HTTP 403 at the edge.
    code, payload = http("POST", "/admin/container-restart", token, None)
    if (code != 202 or payload.get("task_id") != h["job_id"]
        or payload.get("production_revision") != production_revision or payload.get("status") != "ACCEPTED"):
        safe_reason = payload.get("error")
        if not isinstance(safe_reason, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", safe_reason):
            safe_reason = "unclassified"
        else:
            safe_reason = safe_reason.lower()
        raise RuntimeError(f"RECOVERY_RESUME_FAILED_HTTP_{code}_REASON_{safe_reason}")

    samples = []
    last_stamp = None
    for attempt in range(max_heartbeat_attempts):
        if attempt:
            sleeper(10)
        state = _load_status(client, bucket, h["job_id"], production_revision)
        if state["status"] == "FAILED":
            raise RuntimeError("RECOVERY_JOB_FAILED_AGAIN")
        if state["status"] == "RUNNING" and state["updated_at"] != last_stamp:
            code, health = http("GET", "/health", token, None)
            samples.append({
                "container_ready": code == 200 and health.get("ready") is True,
                "machine_ready": True,
                "job_status": "RUNNING",
            })
            last_stamp = state["updated_at"]
            if healthy_after_restart(samples):
                result = {"decision": "RESUME", "reason": "VALIDATED_RECOVERY", "recovered": True,
                          "production_revision": production_revision}
                _persist_recovery(client, bucket, h, result)
                return result
        if state["status"] == "COMPLETED":
            break

    raise RuntimeError("RECOVERY_TWO_RUNNING_HEARTBEATS_NOT_PROVEN")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--production-revision", choices=("v3", "v4"), default=DEFAULT_PRODUCTION_REVISION)
    args = parser.parse_args()
    handoff = {
        "schema": "AGENT21-TO-AGENT11-RECOVERY-V1",
        "repair_id": args.repair_id,
        "job_id": args.job_id,
        "stage_id": args.stage_id,
        "machine": "private-media-container",
        "checkpoint": args.checkpoint,
        "restart_required": True,
        "requested_action": "RESUME",
    }
    client, bucket = client_from_env()
    result = execute_recovery(client, bucket, handoff, os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN", ""),
                              production_revision=args.production_revision)
    print("PRODUCTION_RECOVERED" if result.get("recovered") else "PRODUCTION_RECOVERY_NO_RESTART")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
