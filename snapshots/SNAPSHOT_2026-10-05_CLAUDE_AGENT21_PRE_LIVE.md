# Edirne22 Snapshot — 05.10.2026 CLAUDE / AGENT 21 PRE-LIVE

Frozen code HEAD: `0b5803324899e498284509238171d26c3e6c8ead`
Recovery branch: `backup/2026-10-05-claude-agent21-pre-live`

## Verifiziert
- PR #404 Claude/CODE Dashboard-Transport auf main gemergt (`8d288e8e5996315e084b0e24cc32e58a86dff179`).
- Sichtbare Dashboard-CODE-Konsole vorhanden; Provider-Secret bleibt serverseitig.
- OpenCode 2.0.21 + Claude-only Read-only-Konfiguration im Containerimage verifiziert.
- Agent-21-Infrastruktur-Gate erweitert; Run #40 / `37352549743` SUCCESS.
- Deploy-Image/Staging repariert; Private-ASR Deploy Run #23 SUCCESS.
- Live-Smoke-Diagnose Run #29 / `37357083689`: HTTP 503 `container_not_ready`.
- Fix am Frozen HEAD: alle Container-Routen starten über denselben secret-versorgten Lifecycle-Gate.
- Run #31 / `37360142879` ist zum Snapshot QUEUED und hat noch keinen Runner; kein Ergebnis behauptet.

## Noch offen
1. Run #31 muss den Fix real deployen/testen.
2. Erforderlicher Beleg: `OPENCODE_CLAUDE_LIVE_OK`.
3. Danach echter Dashboard-CODE-E2E.
4. Danach privater Produktionsfall `Dünya – Level 12` (`f6f50c9f4c2690e4eb1fe978`) und evidenzbasierte Agent-21-Beobachtung.

## Zielarchitektur
`Dashboard → Cloudflare Worker/Service Binding → privater Container → OpenCode → OpenRouter → Claude Sonnet 4.5 → Dashboard`

Keine automatische Modellumschaltung. Private Medien privat. Keine Social-Veröffentlichung ohne Human Authority. Guardrails zuerst.
