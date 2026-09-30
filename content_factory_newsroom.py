"""Block 4: provider-independent Research + Facts newsroom.

This module turns untrusted source material into an evidence-bound fact package.
It does not write captions, approve content, or publish.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
import unicodedata
from urllib.parse import urlparse
from typing import Iterable, Optional


class SourceKind(str, Enum):
    ARTICLE = "article"
    TRANSCRIPT = "transcript"
    OFFICIAL = "official"


class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    CONFLICTED = "conflicted"
    RUMOR = "rumor"
    UNSUPPORTED = "unsupported"


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).replace("ı", "i")
    return "".join(c for c in value if not unicodedata.combining(c)).casefold()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    url: str
    title: str
    text: str
    kind: SourceKind = SourceKind.ARTICLE
    publisher: str = ""
    published_at: str = ""
    series: str = ""
    provenance: str = ""

    def __post_init__(self):
        if not self.source_id.strip():
            raise ValueError("source_id required")
        parsed = urlparse(self.url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("source URL must be absolute http(s)")
        if not _clean_text(self.title) or not _clean_text(self.text):
            raise ValueError("source title and text required")
        if len(self.text) > 2_000_000:
            raise ValueError("source text exceeds newsroom safety limit")

    @property
    def fingerprint(self) -> str:
        payload = "\n".join((self.url.strip(), _clean_text(self.title), _clean_text(self.text)))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Evidence:
    source_id: str
    quote: str

    def __post_init__(self):
        if not self.source_id.strip() or not _clean_text(self.quote):
            raise ValueError("evidence requires source_id and quote")


@dataclass(frozen=True)
class FactClaim:
    claim_id: str
    statement: str
    status: ClaimStatus
    evidence: tuple[Evidence, ...] = ()
    series: str = ""
    subjects: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self):
        if not self.claim_id.strip() or not _clean_text(self.statement):
            raise ValueError("claim_id and statement required")


@dataclass(frozen=True)
class FactPackage:
    package_id: str
    story_key: str
    series: str
    sources: tuple[ResearchSource, ...]
    claims: tuple[FactClaim, ...]
    coverage_complete: bool
    conflicts: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def writer_facts(self) -> tuple[FactClaim, ...]:
        return tuple(c for c in self.claims if c.status == ClaimStatus.VERIFIED)

    @property
    def publishable(self) -> bool:
        return (
            self.coverage_complete
            and bool(self.writer_facts)
            and not any(c.status in (ClaimStatus.CONFLICTED, ClaimStatus.UNSUPPORTED) for c in self.claims)
        )

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "story_key": self.story_key,
            "series": self.series,
            "sources": [
                {**s.__dict__, "kind": s.kind.value, "fingerprint": s.fingerprint}
                for s in self.sources
            ],
            "claims": [
                {
                    **c.__dict__,
                    "status": c.status.value,
                    "evidence": [e.__dict__ for e in c.evidence],
                    "subjects": list(c.subjects),
                }
                for c in self.claims
            ],
            "coverage_complete": self.coverage_complete,
            "conflicts": list(self.conflicts),
            "warnings": list(self.warnings),
        }


class NewsroomContractError(ValueError):
    pass


def attach_fact_package(job, package: FactPackage) -> None:
    """Attach immutable newsroom output to a pre-human ProductionJob.

    The newsroom has no authority to approve, queue, or publish. Existing
    package data for the same job/revision cannot be silently replaced.
    """
    status = getattr(job.status, "value", str(job.status))
    if status in ("ready_for_human", "approved", "publish_queued", "published", "rejected"):
        raise NewsroomContractError("fact package cannot mutate a human/finalized job")
    payload = package.to_dict()
    slot = f"fact_package:r{job.revision}"
    existing = job.metadata.get(slot)
    if existing is not None and existing != payload:
        raise NewsroomContractError("fact package replacement requires a new job revision")
    job.metadata[slot] = payload


class FactNewsroom:
    """Validates evidence supplied by research/extraction adapters.

    LLMs may propose claims/evidence, but this deterministic boundary verifies
    that every evidence quote exists verbatim in its declared immutable source.
    """

    def build_package(
        self, *, story_key: str, series: str, sources: Iterable[ResearchSource],
        claims: Iterable[FactClaim], coverage_complete: bool,
    ) -> FactPackage:
        source_list = tuple(sources)
        claim_list = tuple(claims)
        if not story_key.strip():
            raise NewsroomContractError("story_key required")
        if not source_list:
            raise NewsroomContractError("at least one source required")
        if not claim_list:
            raise NewsroomContractError("at least one claim required")

        by_id = {}
        fingerprints = set()
        for source in source_list:
            if source.source_id in by_id:
                raise NewsroomContractError("duplicate source_id")
            if source.fingerprint in fingerprints:
                raise NewsroomContractError("duplicate source content")
            by_id[source.source_id] = source
            fingerprints.add(source.fingerprint)

        claim_ids = set()
        conflicts = []
        warnings = []
        for claim in claim_list:
            if claim.claim_id in claim_ids:
                raise NewsroomContractError("duplicate claim_id")
            claim_ids.add(claim.claim_id)
            if claim.series and series and claim.series != series:
                raise NewsroomContractError(
                    f"claim series {claim.series} conflicts with locked story series {series}"
                )
            if claim.status == ClaimStatus.VERIFIED and not claim.evidence:
                raise NewsroomContractError(f"verified claim {claim.claim_id} has no evidence")
            for evidence in claim.evidence:
                source = by_id.get(evidence.source_id)
                if source is None:
                    raise NewsroomContractError("evidence references foreign source")
                haystack = _fold(source.title + " " + source.text)
                if _fold(_clean_text(evidence.quote)) not in haystack:
                    raise NewsroomContractError(
                        f"evidence quote not found in source for {claim.claim_id}"
                    )
            if claim.status == ClaimStatus.CONFLICTED:
                conflicts.append(claim.claim_id)
            elif claim.status == ClaimStatus.RUMOR:
                warnings.append(f"rumor:{claim.claim_id}")
            elif claim.status == ClaimStatus.UNSUPPORTED:
                warnings.append(f"unsupported:{claim.claim_id}")

        canonical = {
            "story_key": story_key, "series": series,
            "sources": sorted((s.source_id, s.fingerprint) for s in source_list),
            "claims": sorted((c.claim_id, c.statement, c.status.value) for c in claim_list),
        }
        package_id = hashlib.sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return FactPackage(
            package_id=package_id, story_key=story_key, series=series,
            sources=source_list, claims=claim_list,
            coverage_complete=bool(coverage_complete),
            conflicts=tuple(conflicts), warnings=tuple(warnings),
        )
