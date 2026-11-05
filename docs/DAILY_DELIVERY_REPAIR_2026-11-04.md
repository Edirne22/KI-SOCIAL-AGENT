# Tagesvorschläge: Reparatur und Abnahme

Auftrag: täglichen 08:00-MotoGP-Vorschlag und den verlinkten Ideengenerator reparieren, nach grünen Prüfungen mergen.

## Belegte Ursachen

- Run 41853312373: allgemeiner Ideengenerator scheitert vor der Inferenz mit R2 `NotEntitled`.
- MotoGP Run 41656638759: Start 14:44 UTC, fünf fertige Vorschläge und neun bestätigte Telegram-Sendungen erst 15:33 UTC. 60 Kandidaten werden vor der Auswahl redaktionell bearbeitet; Provider-429 und Reparaturschleifen verlängern diesen Abschnitt.
- Morgen-Controller sperrt ein nach Runner-Abbruch persistiertes STARTED bisher dauerhaft für diesen Tag.

## Umfang

- Daily Ideas wählt ausdrücklich vorhandene Git-versionierte Rollen-/Memory-Dateien als Kontext. Fehlende, leere, übergroße Dateien und ungültige IDs blockieren; keine private R2-Historie wird kopiert oder als geladen behauptet. Explizit gewähltes R2 bleibt fail-closed.
- Racing qualifiziert in Fünfergruppen bis zu fünf vollständig finalisierten Paketen. Alle Copy-, Fakten-, Batch-, Media- und Chief-Gates bleiben aktiv; maximal 60 aktuelle und 20 Vortagskandidaten.
- 08:00 Europe/Berlin bleibt Haupttermin. 08:17, 09:17, 10:17 sind begrenzte Recovery-Termine. Erledigte Tage werden vor Installationen übersprungen; Workflow-Concurrency verhindert parallele Produzenten. STARTED ist nach dem bestehenden 90-Minuten-Timeout erneut ausführbar.

Nicht-Ziele: neue Hosting-Dienste, Kosten, private R2-Migration, Änderungen an Publishing-Autorität, Turkish-Rider-Zeitfenster oder Quellenwahrheit. GitHub-Schedule-Verzögerungen können durch Repository-Code nicht ausgeschlossen werden; minutengenaue Zustellung wird nicht zugesichert.

## Endliche Abnahmematrix (vor Implementierungs-Commit)

| Kriterium | Nachweis |
| --- | --- |
| R2-Ausfall reproduziert; Repository-Kontext ohne R2 | test_daily_delivery_recovery; Original-Run |
| Fehlendes/leeres/übergroßes Memory, Path Traversal blockiert | test_daily_delivery_recovery |
| Gültige Pläne/Provider-Fallback; ungültige Pläne blockiert | test_quality_daily_recovery |
| Fünf fertige Pakete stoppen weitere Inferenz | test_daily_delivery_recovery |
| Copy-/Batch-/Media-Reject führt zum nächsten Kandidaten | test_daily_delivery_recovery |
| Duplikate über Gruppen; 60/20-Grenzen; Vortagsreserve | test_daily_delivery_recovery |
| Sommer/Winter, verspäteter Cron, einmal pro Tag, manueller Start | test_racing_morning_repair; test_racing_manual_rerun |
| Abbruch/STARTED-Recovery; serialisierte Ausführung | test_daily_delivery_recovery |
| Persistenz vor Telegram; Owner-/Freigabegrenzen | test_daily_delivery_recovery; test_telegram_schedule_recovery |
| Falsche Fakten/Serien/Claims bleiben blockiert; Positivkontrollen | test_source_fact_contract_v1; racing_final_guard_selftest; racing_pipeline_selftest; racing_v85_selftest |
| CI auf finalem PR-Head | GitHub-Checks vor Merge prüfen |
| Echter Daily-Ideas-Lauf nach Merge | Original-Run erneut starten und Ergebnis prüfen |
| Echte neue Racing-Zustellung | Produktionslauf/Logs getrennt von Offline-Tests prüfen; nur tatsächliche Sendebelege als LIVE ausweisen |
| Private Medien und Social-Publishing | N/A: unverändert, kein Veröffentlichungsauftrag |

Die Tests sind Offline-/Vertragstests. Sie belegen weder Provider-Verfügbarkeit noch einen zukünftigen pünktlichen Cron-Start.
