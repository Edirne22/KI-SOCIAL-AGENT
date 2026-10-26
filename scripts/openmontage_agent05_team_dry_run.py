"""Agent 05 live-source team handoff; stop strictly before video production."""
from __future__ import annotations

from scripts.openmontage_agent05_live_sources import fetch_primary_sources
from scripts.openmontage_agent_chain_audit import audit_agent_chain
from scripts.openmontage_quickshifter_research import quickshifter_research


def run_quickshifter_team_dry_run(*, session=None) -> dict:
    source_result = fetch_primary_sources("Wie funktioniert ein Quickshifter?", session=session)
    if source_result["status"] != "EVIDENCE_COLLECTED":
        return {"status": "BLOCKED_NO_LIVE_SOURCES", "source_result": source_result,
                "trace": [{"agent": "05_research_synthesist", "status": "blocked"}],
                "production_started": False}
    # Legacy statements are NOT asserted as independently verified by the live
    # fetch. Attach live source evidence for human review and retain provenance.
    research = quickshifter_research()
    evidence_urls = {item["url"] for item in source_result["evidence"]}
    for story in research["stories"]:
        story["live_evidence_urls"] = sorted(evidence_urls)
        story["live_evidence_status"] = "source_retrieved_claim_not_cross_checked"
    audit = audit_agent_chain(research)
    audit["source_result"] = source_result
    audit["trace"][0]["status"] = "live_sources_handed_off"
    audit["trace"][0]["source_count"] = len(source_result["evidence"])
    audit["status"] = "BLOCKED_CLAIM_VERIFICATION_AND_MEDIA"
    audit["production_started"] = False
    return audit
