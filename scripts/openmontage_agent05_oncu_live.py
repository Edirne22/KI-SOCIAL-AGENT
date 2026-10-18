"""Agent 05 real, bounded Öncü news discovery via existing research gateway.

No synthetic stories, no publication, and search URLs are not verified claims.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra" / "private-asr"))
from research_gateway import research

QUERIES = (
    "Deniz Öncü latest Moto2 news October 2026 official MotoGP team",
    "Can Öncü latest WorldSSP news October 2026 official WorldSBK team",
    "Deniz Öncü 2027 team transfer official announcement",
    "Can Öncü 2027 team transfer official announcement",
)

def run(search=research):
    attempts, findings, seen = [], [], set()
    for query in QUERIES:
        try:
            response = search(query)
            rows = response.get("results") or []
            attempt = {"query": query, "provider": response.get("provider"),
                       "live_search": response.get("live_search") is True,
                       "warning": response.get("warning"), "result_count": len(rows)}
            attempts.append(attempt)
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
    return {"agent": "05_research_synthesist", "topic": "Deniz Öncü und Can Öncü",
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
