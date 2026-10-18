"""Agent 05 real, bounded Öncü news discovery via existing research gateway.

No synthetic stories, no publication, and search URLs are not verified claims.
"""
from __future__ import annotations
import json
import os
import requests
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "infra" / "private-asr"))
from concurrent.futures import ThreadPoolExecutor
from integrations.openmontage.motorsport_source_catalog import SOURCES


def _fetch_official_source(source):
    try:
        response = requests.get(source["url"], timeout=(8, 20), headers={
            "User-Agent": "Mozilla/5.0 (compatible; Agent05Research/1.0)"})
        if response.status_code != 200:
            return None
        return {"title": source["name"] + " (official source entry)",
                "url": source["url"], "snippet": "", "source_checked_http": 200, "source_kind": "homepage_only"}
    except requests.RequestException:
        return None


def research(query):
    """Fetch registered official motorsport sources, with no LLM search quota."""
    key = query.casefold()
    if any(word in key for word in ("deniz", "can öncü", "oncu", "moto2", "motogp")):
        names = {"MotoGP", "MotoGP results", "WorldSBK", "FIM"}
    elif any(word in key for word in ("worldssp", "worldsbk", "superbike")):
        names = {"WorldSBK", "FIM", "Turkish Motorcycle Federation"}
    else:
        names = {"MotoGP", "WorldSBK", "FIM", "Turkish Motorcycle Federation"}
    selected = [source for source in SOURCES if source["tier"] == "official" and source["name"] in names]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_fetch_official_source, selected))
    rows = [item for item in results if item]
    return {"live_search": bool(rows), "provider": "OfficialSourceDirect",
            "results": rows, "warning": None if rows else "OFFICIAL_SOURCES_UNREACHABLE"}

QUERIES = (
    "Deniz Öncü latest Moto2 news October 2026 official MotoGP team",
    "Can Öncü latest WorldSSP news October 2026 official WorldSBK team",
    "Deniz Öncü 2027 team transfer official announcement",
    "Can Öncü 2027 team transfer official announcement",
)

def _nemotron_assess(findings):
    """Analyze discovery candidates, never certify claims from model output."""
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not key:
        return {"status": "NVIDIA_KEY_MISSING"}
    if not findings:
        return {"status": "NO_SOURCES_TO_ASSESS"}
    payload = [{"title": x["title"], "url": x["url"]} for x in findings[:8]]
    try:
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            json={"model": os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
                  "messages": [{"role": "user", "content":
                    "Assess relevance and identify which original sources require reading. "
                    "Do not claim any source was verified. Candidate URLs: " + json.dumps(payload)}],
                  "max_tokens": 600, "temperature": 0.2, "stream": False},
            timeout=(20, 120),
        )
        if response.status_code != 200:
            return {"status": "NVIDIA_HTTP_" + str(response.status_code)}
        content = response.json()["choices"][0]["message"]["content"]
        return {"status": "ASSESSMENT_UNVERIFIED", "summary": str(content)[:2500]}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return {"status": "NVIDIA_REQUEST_FAILED"}


def run(search=research, queries=QUERIES, assess=_nemotron_assess):
    attempts, findings, seen = [], [], set()
    for query in queries:
        try:
            response = search(query)
            rows = response.get("results") or []
            attempt = {"query": query, "provider": response.get("provider"),
                       "live_search": response.get("live_search") is True,
                       "warning": response.get("warning"), "result_count": len(rows)}
            attempts.append(attempt)
            if "429" in str(attempt["warning"] or ""):
                # Stop instead of hammering an exhausted free-tier quota.
                break
            if not attempt["live_search"]:
                continue
            for row in rows:
                url = str(row.get("url") or "")
                if not url.startswith("https://") or url in seen:
                    continue
                seen.add(url)
                findings.append({"query": query, "title": row.get("title"),
                                 "url": url, "snippet": row.get("snippet"),
                                 "claim_verified": False, "media_rights_verified": False})
        except Exception as exc:
            attempts.append({"query": query, "live_search": False,
                             "warning": type(exc).__name__, "result_count": 0})
    # Candidate discovery only: linked pages are not licensed downloadable assets.
    media_candidates = []
    for item in findings:
        host = (urlsplit(item["url"]).hostname or "").lower()
        if any(domain in host for domain in ("worldsbk.com", "motogp.com", "yamaha-racing.com", "marcvds.com")):
            media_candidates.append({
                "source_url": item["url"], "title": item["title"],
                "media_type": "video_page" if "/video" in urlsplit(item["url"]).path else "editorial_page",
                "direct_media_url": None, "media_rights_verified": False,
                "usage": "discovery_only", "needs_license_review": True,
            })
    assessment = assess(findings)
    return {"nvidia_assessment": assessment, "media_candidates": media_candidates,
            "media_status": "CANDIDATES_UNLICENSED" if media_candidates else "NO_MEDIA_CANDIDATES",
            "agent": "05_research_synthesist", "topic": " | ".join(queries),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "status": "DISCOVERY_COMPLETE_UNVERIFIED" if findings else "BLOCKED_NO_LIVE_SEARCH",
            "attempts": attempts, "findings": findings,
            "handoff": "FACT_CHECK_REQUIRED", "production_started": False,
            "publication_authorized": False}

if __name__ == "__main__":
    output = run()
    Path("agent05-oncu-report.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "attempts": output["attempts"],
                      "findings": output["findings"]}, ensure_ascii=False))
    if not output["findings"]:
        raise SystemExit("No live search results; report retained for diagnosis")
