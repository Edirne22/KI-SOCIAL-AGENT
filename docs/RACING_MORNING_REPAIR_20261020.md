# Racing-Morgenlauf: Diagnose und Abnahmematrix, 20.10.2026

Basis: 20a80d72bff88bb164baa405262f5a1b2c37ab14.

## Belegte Ursachen

- Run https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/39225574009 wurde am 19.10. erst 08:49:55 UTC angelegt. Verarbeitung ab 08:51:31 UTC. Discovery 572.539 s, Artikelabruf 798.184 s, Redaktion/QM 1303.239 s, Gesamt 2773.864 s. Die zwei bestehenden UTC-Crons verhinderten die verspätete Auslösung nicht.
- 909 Rohlinks, 730 nach Vorfilter, aber nur die ersten 320 abgerufen. Davon 253 älter als sieben Tage. Später entdeckte Quellen wurden unabhängig von ihrer Aktualität abgeschnitten.
- Turkish-Recherche umgeht den normalen Discovery-Dedupe absichtlich; nach Anreicherung fehlte die erneute Sperre. Der Vortagespool sperrte nur veröffentlichte, nicht bereits angebotene Stories. Titeländerungen konnten nicht-MotoGP-URLs erneut zulassen.
- Turkish: Drei-Tage-Fenster und bis zu 20 dauerhaft als angeboten markierte Kandidaten bei nur fünf sichtbaren Vorschlägen. Im belegten Lauf zwei datumsseitig passende türkische Artikel, aber null eigenständige Vorschläge nach Ausschlüssen.

## Änderung

Genau ein täglicher GitHub-Zeitplan: `cron: "0 8 * * *"`, `timezone: "Europe/Berlin"`. Native Zeitzonenplanung berücksichtigt Sommer-/Winterzeit ohne zusätzliche Aufweckläufe. Das vorhandene Europe/Berlin-Gate erlaubt Verarbeitung ab 08:00 auch bei verspätetem Start nach 12:00. Nach erfolgreichem Tagesbatch kein erneuter teurer Lauf. Manuelle Starts bleiben möglich. Ein GitHub-Schedule ist keine garantierte 08:00-Zustellung; die Redaktion braucht zusätzlich Laufzeit.

Alle entdeckten vorgefilterten Artikel werden mit maximal sechs gleichzeitigen Abrufen verarbeitet. Gemeinsame Titel-/URL-Dedupe vor Redaktion, Vortagesfallback und finaler Auswahl. Turkish sucht bis sieben Tage, markiert zunächst nur die sichtbaren fünf; explizites `turkish liste` markiert die tatsächlich gesendete Liste. Quellen-/Fakten-QM und Publishing-Freigaben unverändert.

## Endliche Abnahme

- Zeit: Sommer/Winter, außerhalb Morgenfenster, Berlin-Tagesidentität, manuell, Wiederanlauf BLOCKED, Tagesduplikat.
- Daten: Quelle hinter Index 320, Reihenfolge/Metadaten, Titeländerung/Tracking-URL, Vortagespool, Turkish-Reinjektion, Racing/Turkish-Doppelangebot.
- Turkish: vier Tage alte valide Quelle akzeptiert; undatiert, zukünftig, >7 Tage gesperrt; unsichtbare Reserve erhalten; Listenversandfehler verbraucht keine Kandidaten; fremder Chat ohne Zugriff.
- Regression: vorhandene Source-Fact-, Final-Guard-, V8.5-, Telegram- und Turkish-Tests. Neue Tests laufen ohne Secrets und ohne Telegram-Versand in CI.
- Live-Abnahme OFFEN: produktiver Morgenlauf auf gemergtem Stand, dessen Phasenzeiten und tatsächlicher Telegram-Empfang. Ein synthetischer Test belegt keine pünktliche GitHub-Auslösung oder täglich verfügbare Nachrichten.
- N/A: neue Infrastruktur, Kosten, Social-Publishing, private Medien. Keine Änderungen an bestehenden Memory-/Content-Dateien.

Keine Garantie für täglich fünf neue reale Meldungen. Fehlende belegte Nachrichten dürfen nicht durch erfundene Nachrichten ersetzt werden.

## Kontingentkorrektur nach Nutzerhinweis

Bülent meldet am 20.10. ein ausgeschöpftes 2000-Minuten-Kontingent. Der Kontostand wurde nicht unabhängig abgerufen; die verspäteten Logs allein beweisen keine Kontingentursache. Zusätzliche Startversuche beheben eine Kontingentsperre nicht und wurden aus diesem PR entfernt. Statt bis zu 15 geplanten Auslösungen pro Tag enthält der Workflow jetzt eine. Keine Änderung an anderen Workflows oder vorhandenen Qualitätsgates.

Syntaxreferenz: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule

Der Folgecommit spart CI-Ausführungen mit `[skip ci]` und bleibt ungemergt. Die 16 erfolgreichen CI-Läufe gehören ausschließlich zum vorherigen Commit `77d7db62096e8d6e5424b28428af3bb691c483de`. Für den neuen Stand wurden Zeitplan und angepasste Testassertion statisch geprüft, aber keine Python-Tests ausgeführt, da die lokale Ausführungsumgebung nicht erreichbar ist. Vor Merge gezielt `PYTHONPATH=. python tests/test_racing_morning_repair.py` mit den Projektabhängigkeiten ausführen und erforderliche CI nachholen.

## Produktionsbefund 23.10.2026

Run 39925177391: 440 vorgefilterte Artikel, nur 320 abgerufen. Turkish-Diagnose enthält drei PASS-Einträge, zahlreiche older-than-window und am Ende sent=0, history=0, max_days=3. Die Auswahl wird zusätzlich durch bereits angebotene bzw. normale Racing-Picks eingeschränkt; aus diesen Logs allein ist die genaue Aufteilung dieser Ausschlüsse nicht ablesbar. Der bisherige Fix war noch nicht auf main.

Das Morgen-Gate lehnt verspätete Starts nach Mittag nicht mehr ab. Tages-Duplikatschutz bleibt bestehen. Die bestehende Zeit-Assertion wurde angepasst, aber auf ausdrücklichen Nutzerwunsch kein Test und keine CI gestartet. Die aktuellen Instagram-/Freigabe-Fixes aus PR 666 und Daily-Ideas-Fixes aus PR 667 liegen auf main; PR 664 ist laut GitHub konfliktfrei damit zusammenführbar. Keine Garantie für fünf täglich neue belegte Meldungen.
