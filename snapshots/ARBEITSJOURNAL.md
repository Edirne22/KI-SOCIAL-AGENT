# KI-SOCIAL-AGENT – Dauerhaftes Arbeitsjournal
Format: UTF-8 Markdown, maschinen- und menschenlesbar.
Dieses Journal ist die operative Übergabe. Für ausführliche historische Architektur siehe MASTER-SNAPSHOT.md und datierte snapshots/.
Regel: Vor einer neuen Arbeit diesen Stand und den neuesten datierten Snapshot lesen; nach jeder belegten Änderung ergänzen. Kein Erfolg ohne Commit/CI-Beleg. Niemals Secrets notieren.
Statuswerte: REQUESTED | IN_PROGRESS | COMMITTED | CI_GREEN | CI_RED | MERGED | BLOCKED | DELEGATED.
Jeder Eintrag: Datum Europe/Berlin, Auftrag, Branch, PR, Commit, Änderung, Test/Run, Status, nächster Schritt.
Nur abgeschlossene und verifizierte PRs als MERGED markieren. Keine nachträglichen unbestätigten Behauptungen.

## 2026-10-19 12:59 Europe/Berlin – Journal eingerichtet
- Auftrag: Dauerhaftes Änderungs- und Wiederaufnahmejournal für jeden künftigen Arbeitsauftrag, insbesondere nach PR-Merge.
- Repository: Edirne22/KI-SOCIAL-AGENT; diese Datei auf main.
- Status: COMMITTED (GitHub-Commit der Erstellung in der Chatantwort verlinkt).
- Regel: Bei neuen Aufgaben zunächst Auftrag mit Status REQUESTED/IN_PROGRESS dokumentieren, bei Änderungen Commits und CI nachtragen, nach Merge endgültig MERGED mit Merge-SHA. Wenn ein Chat endet, offenes NEXT festhalten.
- Hinweis: Kein unsichtbarer Dauerprozess; Aktualisierung erfolgt bei tatsächlichen Chat-Arbeitsschritten. Stündliche Statusautomatisierung ist separat und schreibt nicht automatisch in GitHub.

## 2026-10-19 12:47 – Jules übernimmt Hermes/OpenMontage
- Auftrag: Reparatur source_reader MISSING_documents, aktiver Faktenprüfer, variable Story-Anzahl, Agent 05 + parallele YouTube/Instagram Scouts, reale OpenMontage-Videos, R2 und Telegram-Verifikation.
- Arbeitsbranch: feature/hermes-coordination-contract; PR #662.
- Faktenprüfer-Commit: 7e9f1728ca273e3cb045c4f583c96d1b558938f6.
- Fehlernachweis: GitHub Actions 39237897383, role=source_reader, MISSING_documents, candidate_claims=0. Faktenprüfer in diesem Run nicht erreicht.
- Historische PRs: #654 (parallel_scout_handoff.py; Runtime-Integration/Instagram-Provider offen), #562 (YouTube Clipanalyse Anforderungen), #655 (HTTPS Medienpfad).
- Stand: DELEGATED an Jules; Screenshot zeigt Einrichtung/Dateilesen, kein belegter Reparatur-Commit oder grüner E2E.
- Konfliktregel: Während Jules dieselben Produktionsdateien bearbeitet, keine konkurrierenden Änderungen.
- NEXT: Jules-Commits und CI prüfen; echten Quellenabruf, Faktencheck, MP4, Untertitel und Telegram-/R2-Status separat nachweisen.

## 2026-10-19 12:37 – Projekt-Recovery-Snapshot
- Datei: snapshots/SNAPSHOT_2026-10-19_HERMES_OPENMONTAGE_HANDOVER.md
- Commit auf main: 7a1360709bda091624cc6ad5b4832ac26c84ef2c
- Status: COMMITTED.
- NEXT: Bei Chatwechsel zuerst neuestes Journal + neuester Snapshot, dann tatsächliche GitHub-Stände prüfen.

## Journal-Rotation – verbindliche Regel (2026-10-19)
- Wenn diese Datei zu groß oder unübersichtlich wird, niemals alte Einträge überschreiben oder löschen.
- Am Ende der aktuellen Datei einen Verweis auf die Fortsetzung setzen: `snapshots/ARBEITSJOURNAL_2.md`.
- Die neue Datei beginnt mit einem Rückverweis auf die vorherige und dem letzten offenen Arbeitsschritt, Branch/PR/Commit sowie dem aktuellen NEXT.
- Danach fortlaufend `ARBEITSJOURNAL_3.md`, `ARBEITSJOURNAL_4.md` usw. ohne feste Obergrenze.
- Beim Neustart stets der Vorwärts-Verweiskette bis zum neuesten Journal folgen, zusätzlich den neuesten datierten Snapshot lesen.
- Jede Rotation ist selbst ein dokumentierter GitHub-Commit; keine unbestätigten Ergebnisse als abgeschlossen markieren.

## 2026-10-19 12:47 Europe/Berlin – Jules Master-Auftrag tatsächlich übergeben (Detailprotokoll)
- Auftraggeber: Nutzer; Ausführung an Google Jules delegiert, Screenshot um 12:47 zeigt eingesetzten vollständigen Prompt und "Setting up the repository..." sowie Lesen von integrations/openmontage/hermes_live_workers.py. Noch KEIN Beweis einer fertigen Reparatur.
- Referenz: PR #662, branch feature/hermes-coordination-contract, checker commit 7e9f1728ca273e3cb045c4f583c96d1b558938f6; Produktionsfehler run 39237897383, source_reader MISSING_documents, candidate_claims=0. Snapshot snapshots/SNAPSHOT_2026-10-19_HERMES_OPENMONTAGE_HANDOVER.md.
- Vollständiger an Jules übergebener Arbeitsumfang (12 Phasen im Chat-Prompt):
  0. Snapshot lesen, kein Full-Repo-Scan, keine unkontrollierte main-Änderung.
  1. Agent Reach Discovery und source_reader reparieren: URLs, Filter, Datumsformate, TR-Sonderzeichen, Quellenkatalog, Fallbacks, Diagnose-Logs; keine unbelegten Quellen durchwinken.
  2. Aktiven Faktenprüfer aus 7e9f1728 prüfen: Original erneut lesen, Korrekturen unabhängig prüfen, CONFIRMED/CORRECTED/UNSUPPORTED; Toprak Türkei/MRT Regression; read_web Schema und fehlende Metadaten absichern.
  3. Starre sechs-Claims-Sperre aus scripts/hermes_toprak_production.py entfernen; 1/2/3/6 Aussagen und dynamische Szenen testen.
  4. Bestehende Social-Agenten REUSE: PR #654 integrations/openmontage/parallel_scout_handoff.py (Agent05/YouTube/Instagram parallele Callables, noch keine komplette Runtime), PR #562 YouTube-Clipanalyse-Anforderungen, motoparktv_video_ingest.py mit Transkription, PR #655 OpenMontage HTTPS-Medienpfad. PR #63/#65 Instagram Engagement ist nicht Scout.
  5. Drei parallele echte Recherchewege (Agent 05, YouTube, Instagram) mit dokumentierter Evidenz/Medienrechte-Klassifikation und ohne vorgetäuschten Plattformzugriff.
  6. OpenMontage: 9:16, echte passend lizenzierte Medien, kreative Szenen, Audio, eingebrannte deutsche Untertitel, nachweisbar valide MP4, keine automatische Veröffentlichung.
  7. Vorhandene R2-Memory-Verträge verwenden, kein neuer Speicher; tatsächliche Schreib-/Lese-Verifikation falls möglich.
  8. Turkish Riders T1 wegen ausbleibender Telegram-Meldungen gezielt auf gemeinsame Filter-/Prüffehler kontrollieren.
  9. Phasen A-H: Quellen, Fakten, variable Stories, Plattform-Scouts, Medienübergabe, MP4, R2/Telegram, E2E; jede Phase mit überprüfbaren Tests/CI.
  10. Credit-Sparmodus: kleine Commits, keine wiederholten Gesamtscans, Free-first, kein Cloudflare-Container, Jarvis separat, keine unautorisierten Merges/Publikationen.
  11. Abschlussbericht mit konkreten Dateien, SHAs, CI-Run-IDs, echten Abrufen, Video-/Untertitel-/R2-/Telegram-Belegen und offenen Punkten.
  12. /BLOCKRUN START, zuerst MISSING_documents reparieren, dann restliche Phasen fortsetzen.
- Status: DELEGATED / IN_PROGRESS (Jules arbeitet; kein verifizierter neuer Commit, kein grüner Produktionslauf, kein Merge).
- Konfliktregel: Während Jules diese Produktionsdateien bearbeitet, keine konkurrierenden Änderungen durch ChatGPT.
- NEXT: Jules-Rückmeldung und GitHub-PR/Commits kontrollieren, echten E2E verifizieren; Ergebnisse hier mit Run-ID/Commit/Status nachtragen.
- Arbeitsjournal-Regel erweitert: Auch an Jules, Work oder andere Agenten delegierte Aufträge und deren nachgewiesene Ergebnisse dokumentieren, nicht nur eigene Codeänderungen. Nie delegiert mit erledigt verwechseln.

## 2026-10-19 15:06 Europe/Berlin – Jules Abschlussmeldung, externe Prüfung vor Einreichung
- Nutzerauftrag: Alle Jules-Steps auf Richtigkeit kontrollieren und Arbeitsjournal aktualisieren.
- Jules-Screenshot: „All plan steps completed – Ready for submission“. Jules behauptet 271 Tests erfolgreich, Code Review bestanden, Änderungen an parallel_scout_handoff.py, OpenMontage, Faktenprüfung, R2-Verträgen und Turkish Riders. Dies sind SELBSTBERICHTETE Ergebnisse, noch nicht GitHub-verifiziert.
- GitHub REST-Prüfung (PR-Liste und jüngste main-Commits): Kein neuer PR nach #662; #662 weiterhin HEAD 7e9f1728ca273e3cb045c4f583c96d1b558938f6. Kein Jules-Fix auf main in jüngsten Commits; aktuelle CI-Beweise für Jules-Änderungen fehlen.
- Review-Status: BLOCKED_PENDING_SUBMISSION. Keine unabhängige Code-Diff-/CI-/Live-E2E-Prüfung möglich, solange Jules die Änderungen nicht auf einen zugänglichen Branch/PR überträgt. Der letzte bestätigte Hermes-Toprak-Lauf 39237897383 scheiterte source_reader MISSING_documents; keine verifizierte echte MP4.
- NEXT: Nutzer/Jules soll „Submit changes“/„Create PR“ ausführen und PR-Link/Commit-SHA mitteilen. Danach Diff-Dateien, Testprotokolle, echte Plattformscouts, 1-6 Claims, R2, Untertitel, Produktion einzeln verifizieren. PR #662 nicht mergen oder veröffentlichen.
