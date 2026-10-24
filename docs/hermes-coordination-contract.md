# Hermes Coordination Contract — KI-SOCIAL-AGENT

Status: design and integration contract only; Hermes runtime is NOT installed or activated.
Upstream: https://github.com/NousResearch/hermes-agent (MIT; review pinned version and dependencies before vendoring).

## Existing architecture
Keep existing GitHub Actions, Telegram approvals, R2 storage, Agent 05, legacy scouts, Nemotron, fact checker and OpenMontage. No VPS, container, paid service or automatic publishing.

## Responsibilities
- Coordinator: classify task as news / evergreen technical / media production; assign bounded subtasks; enforce dependency graph and source requirements.
- Research: Agent Reach (after separate license/security assessment) + existing official source catalog and scouts; retrieve actual articles, not category pages.
- Analysis: NVIDIA Nemotron processes source text and returns evidence with URL and quoted supporting excerpt; model output is never itself evidence.
- Verification: existing fact checker must reject zero supported factual claims; distinguish evergreen product history from current news.
- Media: OpenMontage may only receive verified material and explicit production intent; no media on research-only requests.
- Publisher: require Telegram owner approval, independent of planning and render permissions.

## Required machine-readable handoff
Each step returns job_id, agent_id, task_type, input_refs, output_refs, evidence_urls, claims, verdict (PASS/RETRY/BLOCK), failure_reason, elapsed_ms, cost_estimate and next_agent. Each claim needs source URL, source text excerpt, source date if available, and confidence classification. Never promote an unchecked discovery URL to a verified fact.

## Coordinator rules
- Only dispatch an agent when predecessor PASS criteria are satisfied.
- RETRY at most twice per step; no repeated unbounded crawling; enforce deadlines and quotas.
- A failed or empty handoff blocks dependent agents; never mark pipeline green merely because a script exited zero.
- Log every assignment and result; provide per-agent metrics for the owner.
- Secrets stay in GitHub Secrets; free-first, no new costs without approval.
- Research-only jobs terminate at evidence report, not storyboard/render/publish.

## Acceptance test: Michelin Power GP first generation
Input: Michelin Power GP V1 (2020), not GP2. Required: dated official source or archival manufacturer document, original model specifications, road/track use and supported grip/pressure statements, plus explicit unknowns. Reject car tire category links and Power GP2-only pages. Output source-backed facts and per-agent audit, zero video artifacts.

## Integration phases
1. Implement contract and simulated coordinator tests in isolated branch.
2. Inspect Hermes subagent and skills APIs, security boundaries and runtime costs; pin version.
3. Adapt coordinator to existing GitHub Actions/R2; run offline dry run.
4. Wire approved Hermes runtime only if hosting and model costs remain within authorized limits.
