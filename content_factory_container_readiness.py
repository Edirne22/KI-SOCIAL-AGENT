"""Shared fail-closed container readiness gate for approved heavy jobs.

Caller authenticates and obtains explicit consent BEFORE invoking. Probe and
dispatch are injected adapters for the SAME pinned container; this helper
never holds a container awake, retries a POST, or logs private payloads.
"""
from dataclasses import dataclass
import time

class ReadinessError(RuntimeError):
    def __init__(self, stage, status=None):
        self.stage, self.status = stage, status
        super().__init__(f"container {stage} failed" + (f" HTTP {status}" if status else ""))

@dataclass(frozen=True)
class DispatchResult:
    status: str
    http_status: int | None = None

def guarded_container_dispatch(*, authorized, consented, probe, dispatch_once,
                               max_probes=3, sleep=lambda _: None):
    """Probe readiness safely, then dispatch exactly once; no blind POST retry."""
    if not authorized or not consented:
        raise PermissionError("container dispatch requires authorization and consent")
    if not callable(probe) or not callable(dispatch_once):
        raise ValueError("pinned container adapters required")
    if type(max_probes) is not int or not 1 <= max_probes <= 5:
        raise ValueError("invalid bounded readiness attempts")
    last = None
    for attempt in range(max_probes):
        try:
            ready, status = probe()
        except Exception:
            ready, status = False, None
        if ready is True and status == 200:
            break
        last = status if type(status) is int and 100 <= status <= 599 else None
        if status in (401, 403, 422, 429):
            raise ReadinessError("readiness_blocked", status)
        if attempt + 1 < max_probes:
            sleep(min(2 ** attempt, 4))
    else:
        raise ReadinessError("not_ready", last)
    try:
        # Never retry: transport failure may mean the job was already accepted.
        status = dispatch_once()
    except Exception as exc:
        raise ReadinessError("dispatch_ambiguous") from exc
    if status == 202:
        return DispatchResult("ACCEPTED_NOT_COMPLETED", status)
    if status == 429:
        raise ReadinessError("rate_limited_no_retry", status)
    if status == 422:
        raise ReadinessError("invalid_request_no_retry", status)
    if status in (401, 403):
        raise ReadinessError("unauthorized_no_retry", status)
    raise ReadinessError("dispatch_unconfirmed", status if type(status) is int else None)
