# Racing Release Evidence Map

Status: binding companion to `PROJECT_GUARDRAILS.md` for major Racing quality changes.

A release/merge-readiness claim must map each in-scope requirement to fresh evidence. A green unit test alone is not runtime proof.

Minimum evidence classes:
- deterministic regression
- hallucination/fake-news attack
- positive control / anti-overblocking
- provider-outage / DEGRADED safety when relevant
- language/human-writing when relevant
- source provenance / fact grounding when relevant
- CI result
- runtime E2E for changes that affect production behavior

The machine-readable schema is `RACING-EVIDENCE-MAP-V1`.
A missing required evidence class is **FAIL/BLOCKED**, never implicit PASS.

Future Quality-Lab stages consume the same evidence map:
1. baseline-vs-candidate agent evaluation
2. source-blind behavior validator
3. racing mutation engine
4. three-model jury for difficult facts

The jury is advisory only. Model consensus can never override deterministic truth gates or source provenance.
