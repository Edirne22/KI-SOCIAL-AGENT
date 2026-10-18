"""Write a human-reviewed agent lesson to private R2 from GitHub Actions.

This CLI does not grant approval. The manual workflow_dispatch is the review
boundary and must only be run by an authorized maintainer.
"""
from __future__ import annotations

import argparse

from integrations.agent_memory_feedback import record_reviewed_outcome
from integrations.openmontage.r2_client import from_environment


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--outcome", required=True,
                        choices=("success", "failure", "lesson", "preference"))
    parser.add_argument("--lesson", required=True)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args(argv)
    result = record_reviewed_outcome(
        from_environment(), agent_id=args.agent_id, job_id=args.job_id,
        outcome=args.outcome, lesson=args.lesson, reviewed=True, share=args.share,
    )
    print(f"Reviewed agent experience persisted for {result['agent_id']}")


if __name__ == "__main__":
    main()
