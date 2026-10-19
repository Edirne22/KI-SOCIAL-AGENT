# MASTER HANDOVER – 2026-10-19 12:37 Europe/Berlin
Repository: Edirne22/KI-SOCIAL-AGENT
READ THIS FIRST for current Hermes/OpenMontage work. Historical MASTER-SNAPSHOT.md and docs/PROJEKT_UEBERGABE.md are older and must not override this checkpoint.

## Objective
Telegram-controlled German/Turkish motorcycle racing content factory. Hermes coordinates; Agent Reach retrieves original sources; Nemotron analyzes; ACTIVE fact checker revisits original URL and corrects grounded wording; shared R2 memory; OpenMontage renders engaging 9:16 real-media clips with burned German subtitles; Telegram preview and owner approval before publishing. Free-first, no paid resources or Jarvis work without consent. No unverified green claims.

## CURRENT IN-PROGRESS BRANCH
feature/hermes-coordination-contract, PR #662. DO NOT MERGE before successful actual production. Last fact-checker change commit 7e9f1728ca273e3cb045c4f583c96d1b558938f6 (2026-10-19), in integrations/openmontage/hermes_live_workers.py. _checker independently re-fetches original articles with Agent Reach/Jina, uses Nemotron to correct or accept, second model review of corrections, logs URLs and hashes. This code has NOT YET BEEN VERIFIED IN PRODUCTION. WARNING: verify read_web return schema for retrieved_at/sha256 before claiming success. The production CI run https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/39237897383 was in progress at 10:35 UTC. Check its final logs and fix defects; add regression tests. The previous run 39235645323 failed fact_checker MISSING_verified_claims, candidate_claims=1 for Toprak Razgatlioglu's return to Turkey for an MRI after Indonesia injury. Previous rejection text truncated. Prior diagnostic commit cbba6ecf. Other earlier green contract tests do NOT prove real video.

## USER'S EXPLICIT FACT-CHECK RULE
Checker must revisit supplied original URL itself; translate Turkish/English appropriately, correct imprecise tense, seek another source when needed, avoid arbitrary rejection. Three outcomes CONFIRMED, CORRECTED, UNSUPPORTED. Exclude unsupported claim only; do not stop whole production if 1-5 verified claims, no mandatory six. No invention of facts or fake rights. User corroborates Toprak example but autonomous verification still uses sources.

## HISTORICAL YOUTUBE / INSTAGRAM FINDINGS – DO NOT REBUILD FROM SCRATCH
PR #654 https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/654 added integrations/openmontage/parallel_scout_handoff.py and tests/workflow. collect_parallel_research(agent05,youtube,instagram) runs three callable lanes concurrently, but DOES NOT itself implement platform providers. PR description says runtime and Instagram provider still pending.
PR #562 https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/562 documents YouTube clip analysis, scene extraction, FFmpeg/OpenMontage handoff as REQUIREMENTS, not finished runtime.
Existing motoparktv_video_ingest.py fetches YouTube @MotoParkTv/videos and discovers IDs, rider recognition, optional transcriber via MOTOPARKTV_TRANSCRIBE_CMD, and turkish_rider_memory.remember_video. It is not proof of a universal YouTube scout.
PR #655 https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/655 connects verified HTTPS media renderer pathway.
Historical PR #63/#65 are Instagram ENGAGEMENT, not automatically Instagram media research.
Need audit actual old scouts, wire real independent YouTube/Instagram discovery in parallel with Agent05 and feed creative director. Avoid confusing Instagram engagement/publisher with scout.

## SOURCE CATALOG / AGENTS / R2
integrations/openmontage/motorsport_source_catalog.py includes official MotoGP, WSBK, FIM, TMF, TRF1 and motoetkinlik. Current agent_reach_adapter.discover searches only TRF1, MotoGP news, WSBK news; read_web allows MotoGP, WSBK, TRF1, MotoEtkinlik. Extend actual live discovery to catalog. skills/content-factory-coordinator/SKILL.md lists seven roles but hermes_live_workers.py currently wires five Python workers (discovery, reader, analyst, checker, handoff), not seven independently spawned Hermes agents. Shared R2 memory in this new path NOT VERIFIED; reuse existing R2 instead of separate storage. Existing Turkish Riders T1 has delivered no messages for days per user; investigate possible shared overblocking without indiscriminate full-repo scan.

## VIDEO
Current scripts/hermes_toprak_production.py produces test/synthetic six-scene MP4 and requires six claims; real third-party racing media, burned subtitles, final end-to-end not yet proven. openmontage_production.py reported subtitles_burned_in=False. User explicitly wants real racing footage and photos, creative narrative, subtitles, preview, publication only after owner approval. docs/OPENMONTAGE_MEDIA_OWNER_POLICY.md has owner media preference, not evidence of rights.

## NEXT STEPS – ORDER
1. Check CI production run 39237897383 and contract tests at commit 7e9f1728. Fix errors in checker (especially fresh read_web schema) and add tests; do not merge #662 while red.
2. Make checker genuinely self-investigating; correct supported claims; independent second source when original ambiguous; no hard six-claim gate.
3. Re-run Toprak actual production, verify real MP4 and logs.
4. Then hand off remaining broad integration to Jules, with PRs #654/#562/#655, source catalog, R2, subtitles, parallel media scouts, T1 problem. Avoid concurrent edits to same files.
5. Verify green CI and explicit owner approval before merge/publish.

## CONTROL / RECOVERY
/BLOCKRUN: status messages do not imply stop; small targeted commits, check CI, repair, no unnecessary full scans, free-first. Read this checkpoint FIRST and inspect ONLY changed areas. Preserve other workflows. Never assert scheduled snapshots commit to GitHub automatically unless an explicit GitHub write automation exists.

## Historical archives
MASTER-SNAPSHOT.md (last top checkpoint Oct 7), docs/PROJEKT_UEBERGABE.md, docs/PROJEKT_UEBERGABE_2026-10-07_DUENYA_V2.md, snapshots/ historical records. Distinguish past facts from current state.

## New-chat startup prompt
/BLOCKRUN – Read snapshots/SNAPSHOT_2026-10-19_HERMES_OPENMONTAGE_HANDOVER.md in Edirne22/KI-SOCIAL-AGENT. Do NOT start over. Check PR #662 HEAD and production run 39237897383, repair remaining checker bugs and verify E2E, then work forward per NEXT STEPS. Preserve all earlier completed work and report exact commit/CI evidence.
