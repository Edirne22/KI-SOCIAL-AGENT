# BACKUP-PROTOKOLL — 04.10.2026 POST-DEDUPE / BLOCK 7–9

## Sicherungspunkt
Gesicherter Git-Code-HEAD: `897c5d0cce44dfe6f17da6783f85c15a35a9a26a`.
Recovery-Branch: `backup/2026-10-04-post-dedupe-block789`.
Dokumentationsbranch: `docs/checkpoint-2026-10-04-post-dedupe`.

Der Recovery-Branch wurde direkt vom oben genannten main-Commit erzeugt. Er enthält damit den Codezustand nach Merge von PR #378 und dient als Rücksprungpunkt vor dem weiteren Block-7/8/9-Ausbau.

## Zugehörige Dokumente
- `MASTER-SNAPSHOT.md` — aktualisierter Haupteinstieg.
- `docs/PROJEKT_UEBERGABE_2026-10-04_POST_DEDUPE_BLOCK789.md` — vollständige Übergabe.
- `snapshots/SNAPSHOT_2026-10-04_POST_DEDUPE_BLOCK789.md` — kompakter eingefrorener Zustand.
- dieses Backup-Protokoll.

## Was diese Sicherung enthält
Getrackten Git-Code, Workflows und Repository-Dokumente bis zum Frozen HEAD. Enthalten sind insbesondere die heute gemergten Publisher-/Turkish-Dedupe-Schutzschichten #377/#378.

## Was diese Sicherung nicht enthält
Keine GitHub-/Cloudflare-Secrets, keine privaten R2-Mediendaten, keine externen Konten, keine Container-Runtime-Zustände, keine ungesicherten Chat-Inhalte und keine Aussage, dass externe Dienste allein durch einen Git-Branch wiederhergestellt werden können.

## Wiederherstellung
Vor einem Restore immer aktuellen main/PR/Actions-Stand prüfen. Recovery-Branch nicht blind auf main force-pushen. Erst vergleichen, Guardrails lesen und nur gezielt wiederherstellen. Private Medien und Social-Publisher bleiben fail-closed.
