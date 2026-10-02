"""Deterministic resource admission prototype for a single local Factory worker.

Important: in-process and ephemeral ONLY. A production distributed scheduler
must put reservations behind shared durable conditional storage (R2 CAS/lease),
with actual measured CPU/GPU/API telemetry. Never mark this prototype LIVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from uuid import UUID, uuid4


class AdmissionError(ValueError):
    """Invalid or contradictory resource reservation."""


@dataclass(frozen=True)
class Capacity:
    cpu: int
    gpu: int
    api: int

    def __post_init__(self):
        for name in ("cpu", "gpu", "api"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise AdmissionError("capacity must contain nonnegative integers")


@dataclass(frozen=True)
class ResourceClaim:
    job_id: str
    revision: int
    task_id: str
    lane: str
    demand: Capacity
    priority: int = 50

    def __post_init__(self):
        try:
            if str(UUID(self.job_id)) != self.job_id:
                raise ValueError
        except (AttributeError, TypeError, ValueError) as exc:
            raise AdmissionError("job_id must be canonical UUID") from exc
        if type(self.revision) is not int or self.revision < 1:
            raise AdmissionError("revision must be positive integer")
        if not isinstance(self.task_id, str) or not (1 <= len(self.task_id) <= 100):
            raise AdmissionError("task_id missing or too long")
        if self.lane not in ("content", "workshop", "research_and_development"):
            raise AdmissionError("unknown job lane")
        if not isinstance(self.demand, Capacity) or not any((
            self.demand.cpu, self.demand.gpu, self.demand.api,
        )):
            raise AdmissionError("require at least one positive demand")
        if type(self.priority) is not int or not (0 <= self.priority <= 100):
            raise AdmissionError("priority must be 0..100")


@dataclass(frozen=True)
class ResourceLease:
    lease_id: str
    claim: ResourceClaim


class LocalResourceManager:
    """Thread-safe local admission; NOT a distributed durable resource manager."""

    def __init__(self, capacity: Capacity, lane_limits=None):
        if not isinstance(capacity, Capacity):
            raise AdmissionError("capacity required")
        self.capacity = capacity
        self.lane_limits = dict(lane_limits or {})
        for lane, value in self.lane_limits.items():
            if lane not in ("content", "workshop", "research_and_development"):
                raise AdmissionError("unknown lane limit")
            if type(value) is not int or value < 1:
                raise AdmissionError("lane limits must be positive")
        self._leases: dict[tuple[str, str], ResourceLease] = {}
        self._lock = RLock()

    def snapshot(self):
        with self._lock:
            consumed = Capacity(
                sum(x.claim.demand.cpu for x in self._leases.values()),
                sum(x.claim.demand.gpu for x in self._leases.values()),
                sum(x.claim.demand.api for x in self._leases.values()),
            )
            return {
                "capacity": self.capacity,
                "used": consumed,
                "active": len(self._leases),
                "by_lane": {
                    lane: sum(x.claim.lane == lane for x in self._leases.values())
                    for lane in ("content", "workshop", "research_and_development")
                },
                "truth": "LOCAL_EPHEMERAL_ONLY",
            }

    def reserve(self, claim: ResourceClaim):
        """Return lease, or None for temporary capacity exhaustion."""
        if not isinstance(claim, ResourceClaim):
            raise AdmissionError("validated ResourceClaim required")
        key = (claim.job_id, claim.task_id)
        with self._lock:
            for active in self._leases.values():
                if active.claim.job_id == claim.job_id and active.claim.revision != claim.revision:
                    raise AdmissionError("stale revision conflicts with active job reservation")
            previous = self._leases.get(key)
            if previous is not None:
                if previous.claim != claim:
                    raise AdmissionError("stale or contradictory active task reservation")
                return previous  # idempotent retry, no double allocation
            state = self.snapshot()
            used = state["used"]
            if any((
                used.cpu + claim.demand.cpu > self.capacity.cpu,
                used.gpu + claim.demand.gpu > self.capacity.gpu,
                used.api + claim.demand.api > self.capacity.api,
            )):
                return None
            if state["by_lane"][claim.lane] >= self.lane_limits.get(claim.lane, 2**31):
                return None
            lease = ResourceLease(str(uuid4()), claim)
            self._leases[key] = lease
            return lease

    def reserve_batch(self, claims):
        """Stable priority order, no preemption, no automatic lease expiry."""
        indexed = list(enumerate(claims))
        if any(not isinstance(claim, ResourceClaim) for _, claim in indexed):
            raise AdmissionError("all claims must be validated")
        # Preflight ALL entries before allocating anything in this batch.
        # Otherwise one late contradictory revision could leave partial leases.
        with self._lock:
            seen = {}
            for _, claim in indexed:
                key = (claim.job_id, claim.task_id)
                previous = seen.get(key) or self._leases.get(key)
                if previous is not None:
                    old_claim = previous if isinstance(previous, ResourceClaim) else previous.claim
                    if old_claim != claim:
                        raise AdmissionError("contradictory duplicate batch claim")
                for prior in seen.values():
                    if prior.job_id == claim.job_id and prior.revision != claim.revision:
                        raise AdmissionError("stale revision within batch")
                for active in self._leases.values():
                    if active.claim.job_id == claim.job_id and active.claim.revision != claim.revision:
                        raise AdmissionError("stale revision conflicts with active reservation")
                seen[key] = claim
            admitted, queued = [], []
            for _, claim in sorted(indexed, key=lambda item: (item[1].priority, item[0])):
                lease = self.reserve(claim)
                (admitted if lease is not None else queued).append(lease or claim)
            return admitted, queued

    def release(self, lease: ResourceLease):
        if not isinstance(lease, ResourceLease):
            raise AdmissionError("exact lease required")
        key = (lease.claim.job_id, lease.claim.task_id)
        with self._lock:
            current = self._leases.get(key)
            if current is None or current != lease:
                raise AdmissionError("missing or foreign lease; never release another task")
            del self._leases[key]
