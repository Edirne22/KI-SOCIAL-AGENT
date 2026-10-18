"""Hourly source freshness snapshots for OpenMontage, stored privately in R2.

A successful HTTP response confirms reachability, not correctness of any
rider, team, result, date or article content. No speculative facts are saved.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from integrations.openmontage.motorsport_source_catalog import SOURCES
from integrations.openmontage.r2_client import from_environment


def snapshot(fetch=None) -> dict:
    def default_fetch(url):
        req = Request(url, headers={"User-Agent": "KI-SOCIAL-AGENT-ResearchMonitor/1.0"})
        with urlopen(req, timeout=12) as response:
            return response.status, response.geturl()
    fetch = fetch or default_fetch
    records = []
    for source in SOURCES:
        url = source["url"]
        try:
            status, final_url = fetch(url)
            expected = urlsplit(url).hostname
            actual = urlsplit(final_url).hostname
            records.append({"name": source["name"], "url": url,
                            "http_status": status,
                            "reachable": status == 200 and actual == expected,
                            "redirect_host": actual if actual != expected else None})
        except Exception as exc:
            records.append({"name": source["name"], "url": url,
                            "reachable": False, "error_type": type(exc).__name__})
    return {"schema": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
            "kind": "source_reachability_only", "facts_verified": False,
            "sources": records}


def main():
    report = snapshot()
    storage = from_environment()
    storage.put_object(
        Key="openmontage/knowledge/source_health_latest.json",
        Body=(json.dumps(report, ensure_ascii=False) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    print(json.dumps({"checked_sources": len(report["sources"]),
                      "reachable_sources": sum(s["reachable"] for s in report["sources"]),
                      "facts_verified": False}))


if __name__ == "__main__":
    main()
