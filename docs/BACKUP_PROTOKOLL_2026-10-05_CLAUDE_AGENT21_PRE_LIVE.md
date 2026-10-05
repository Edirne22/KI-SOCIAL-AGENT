# BACKUP-PROTOKOLL — 05.10.2026 CLAUDE / AGENT 21 PRE-LIVE

## Sicherungspunkt
Frozen Git-Code-HEAD: `0b5803324899e498284509238171d26c3e6c8ead`
Recovery-Branch: `backup/2026-10-05-claude-agent21-pre-live`

Der Recovery-Branch wurde direkt von diesem main-Commit angelegt. Er friert den Codezustand nach dem Lifecycle-Fix ein, bevor Run #31 den Fix real ausgeführt hat.

## Zugehörige aktuelle Dokumente
- `MASTER-SNAPSHOT.md`
- `docs/PROJEKT_UEBERGABE_2026-10-05_CLAUDE_AGENT21.md`
- `snapshots/SNAPSHOT_2026-10-05_CLAUDE_AGENT21_PRE_LIVE.md`
- dieses Backup-Protokoll
- `README.md` und `INDEX.md` als Navigation

## Beweisstatus beim Backup
Agent-21-Gate ist belegt grün. Claude/OpenCode-Transport ist implementiert, aber der reale Claude-E2E ist noch NICHT grün. Letzter diagnostizierter Livefehler: Run #29 HTTP 503 `container_not_ready`. Fix liegt am Frozen HEAD. Run #31 ist QUEUED ohne Runner/Steps; deshalb kein PASS behaupten.

## Nicht enthalten
Keine GitHub-/Cloudflare-Secrets, keine privaten R2-Medien, keine externen Konten, kein Cloudflare-Runtimezustand, keine Modell/API-Schlüssel. Ein Git-Branch allein stellt diese externen Zustände nicht wieder her.

## Restore
Nicht force-pushen. Zuerst aktuellen main, Guardrails und Actions vergleichen; dann gezielt wiederherstellen. Private Medien und Publisher bleiben fail-closed.
