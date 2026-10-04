"""Central technical incident contract for Agent 21 (Factory Maintenance).

This module is deliberately deterministic: it records bounded technical events and
classifies recovery vs coding escalation. It does not itself grant GitHub, publish,
provider, cost, or private-media authority.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json, re

SCHEMA="FACTORY-MAINTENANCE-EVENT-V1"
STATES={"FAILED","STALLED"}
MACHINES={"private-media-container","ai-central-dashboard","ai-central-router"}
CODE_ERRORS={"SyntaxError","NameError","TypeError","ValueError","TimeoutExpired"}
OPS_ERRORS={"READINESS_TIMEOUT","HTTP_UNREACHABLE","CONTAINER_SLEEP","RATE_LIMIT","TRANSIENT_HTTP"}

@dataclass(frozen=True)
class MaintenanceEvent:
    incident_id:str
    machine_id:str
    state:str
    error_class:str
    stage:str=""
    task_id:str=""
    heartbeat_at:str=""
    detail:str=""

def classify(event:MaintenanceEvent)->str:
    if event.state not in STATES or event.machine_id not in MACHINES:
        return "REJECT"
    if event.error_class in OPS_ERRORS:
        return "RECOVERY"
    if event.error_class in CODE_ERRORS:
        return "CODING_ROUTER"
    return "DIAGNOSE"

def persist(client,bucket,event:MaintenanceEvent):
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}",event.incident_id):
        raise ValueError("invalid incident id")
    now=datetime.now(timezone.utc).isoformat()
    payload={"schema":SCHEMA,"agent":"21_factory_maintenance","created_at":now,
             **{k:(str(v)[:300] if k=="detail" else v) for k,v in asdict(event).items()},
             "decision":classify(event)}
    # Immutable-by-key event history: every incident/event gets a unique id.
    key=f"ai-central/v1/maintenance/events/{now[:10]}/{event.incident_id}.json"
    client.put_object(Bucket=bucket,Key=key,Body=json.dumps(payload).encode(),
                      ContentType="application/json",CacheControl="private, no-store",
                      IfNoneMatch="*")
    return payload
