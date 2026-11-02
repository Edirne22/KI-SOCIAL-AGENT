# Hermes / Agent Reach GitHub Actions rollout

Status: opt-in upstream audit and coordinator contract tests only. Production agents unchanged.

## Stage 0 — completed in this branch
- Fail-closed coordination contract and Hermes-compatible skill.
- Agent Reach availability/doctor adapter.
- Unit tests for blocking absent workers and unsupported claims.
- Manual GitHub Actions smoke workflow checks upstream source reachability and contract tests; no third-party installer executes.

## Stage 1 — required before actual runtime install
- Review official upstream installation instructions, LICENSE, dependencies and security permissions.
- Pin both upstream projects to immutable commit SHAs; review downloaded source before executing.
- Confirm Hermes supports a noninteractive, one-shot command with configured NVIDIA provider; no persistent gateway.
- Check Agent Reach safe install and doctor flags against the pinned release.
- Isolate secrets; never pass GitHub token to research scraping tools.

## Stage 2 — staged wiring
- Build actual adapters from current scout, source reader, Nemotron and fact checker to the coordinator's worker contract.
- Persist coordinator handoffs to private R2 with per-agent provenance and job id.
- Execute one Michelin Power GP V1 research-only E2E test.
- Compare shadow output with legacy pipeline. Block on missing evidence, irrelevant URLs or model failures.

## Stage 3 — canary and rollback
- Enable Hermes coordination for one nonpublishing job, behind HERMES_COORDINATOR_ENABLED=false by default.
- Validate real task dispatch and evidence quality, then enable one scheduled workflow at a time.
- Retain rollback to existing GitHub Actions dispatch and owner-only Telegram publishing approval.

GitHub Actions is ephemeral: it cannot provide an always-on Hermes Telegram gateway. Do not claim all agents are migrated until each scheduled production entry point invokes and successfully completes the new coordinator.
