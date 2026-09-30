# OPENCHATCUT BLOCK 6 – QUICK HANDOVER – 2026-09-30 22:49

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN

Vor Arbeiten zuerst `PROJECT_GUARDRAILS.md` lesen. Danach `MASTER-SNAPSHOT.md` und `snapshots/SNAPSHOT_2026-09-30_OPENCHATCUT_BLOCK6_LIVE_CANDIDATE.md`.

Aktiver Modus: `/BLOCKRUN`. Nicht an Commit, PR, grünem Einzeltest oder Statusmeldung stoppen. ROT → Logs → Root Cause → Fix → erneut testen. SIMULATED niemals LIVE nennen.

## Wiederaufnahme in einem Satz

Main `e5db9ab93e6eeea721145fb4585613107379feb7`; OpenChatCut Cloudflare-PoC ist deployed und bis create/target project real verifiziert, aber `begin_edit_session` erzeugte einen Cloudflare-Disconnect; PR #259 instrumentiert einen frischen MCP-/Persistenz-Probe, Produktionslauf `36773936472` entscheidet als Nächstes Restart/State-Verlust vs. Transportproblem.

## Danach

Disconnect beheben → R2-Input/import/edit/commit → native headless export → ffprobe → R2/SHA → 7/15/30-s Benchmarks mit Caption+Audio → Negative/Retry/Resume → erst dann OpenChatCutAdapter LIVE → SupoClip LIVE → Gesamtstaffel.
