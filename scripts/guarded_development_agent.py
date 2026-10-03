"""Bounded development-agent planner. Never executes task text or modifies repository."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ALLOWED = {
    369: {
        "title": "Private Telegram album project intake",
        "paths": [
            "scripts/telegram_private_media.py",
            "scripts/r2_media_warehouse.py",
            "telegram_router.py",
            "tests/test_telegram_private_media.py",
            "tests/test_r2_media_warehouse.py",
        ],
        "checks": [
            "python -m unittest discover -s tests -p test_telegram_private_media.py -v",
            "python -m unittest discover -s tests -p test_r2_media_warehouse.py -v",
        ],
        "constraints": [
            "Do not forward private album items to legacy vision or social pipelines",
            "R2 immutable originals, readback SHA256 and compare-and-swap manifests",
            "Album correlation by chat and media_group_id, never timestamp alone",
            "No private files or secrets in GitHub artifacts or model prompts",
            "No production deployment or automatic merge",
        ],
    }
}

def plan(issue: int) -> dict:
    if issue not in ALLOWED:
        raise ValueError("Development issue is not allowlisted")
    spec = ALLOWED[issue]
    missing = [path for path in spec["paths"] if not Path(path).is_file()]
    return {
        "schema": "GUARDED-DEVELOPMENT-PLAN-V1",
        "issue": issue,
        **spec,
        "status": "BLOCKED_MISSING_SOURCE" if missing else "PLAN_ONLY_AWAITING_CODE_REVIEW",
        "missing_prerequisites": missing,
        "automatic_commit": False,
        "automatic_merge": False,
        "automatic_deploy": False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", required=True, type=int)
    parser.add_argument("--output", default="guarded-development-plan.json")
    args = parser.parse_args()
    result = plan(args.issue)
    destination = Path(args.output)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"GUARDED_PLAN_PASS issue={args.issue} status={result['status']}")

if __name__ == "__main__":
    main()
