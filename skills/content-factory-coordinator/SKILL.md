---
name: content-factory-coordinator
description: Coordinates research, evidence checking and controlled production for KI-SOCIAL-AGENT
version: 0.1.0
platforms: [linux]
---
# Content Factory Coordinator (Hermes compatible)
## Authority
The coordinator assigns work; it does not certify facts. Owner Telegram approval is mandatory for publication.
## Agent responsibilities
1. Research discovery: use Agent Reach channels when installed and available; otherwise existing scouts. Return relevant candidate URLs.
2. Source reader: fetch original article body and provenance. Reject category pages and off-topic links.
3. Nemotron analyst: extract candidate claims with explicit source references; never invent evidence.
4. Fact checker: verify each claim against retrieved source excerpts. Empty confirmed facts means BLOCK.
5. Handoff: prepare evidence report for the next agent only after PASS.
6. Creative director / storyboard / video renderer: activate only on explicit production requests and verified source evidence.
7. Publisher: never post without owner approval.
## Failure rules
Stop on missing worker, missing evidence, quota exhaustion, deadline or repeated failures. Maximum one retry by default. Do not silently skip.
## Verification
For a Michelin Power GP V1 research-only job, return verified V1-specific sources or BLOCK; no video or publication.
