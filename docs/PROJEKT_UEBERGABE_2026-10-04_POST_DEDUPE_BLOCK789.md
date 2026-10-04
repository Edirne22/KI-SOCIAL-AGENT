# Edirne22 Projektübergabe — 04.10.2026, nach Publisher-Dedupe-Hardening

## Verifizierte Basis
Repository: `Edirne22/KI-SOCIAL-AGENT`

Code-Sicherungs-HEAD vor dieser Dokumentationsaktualisierung:
`897c5d0cce44dfe6f17da6783f85c15a35a9a26a`

Recovery-Branch:
`backup/2026-10-04-post-dedupe-block789`

Verbindlich bleiben `PROJECT_GUARDRAILS.md`, `MASTER-SNAPSHOT.md` und `docs/TOOL_INDEX.md`. Dieser Checkpoint ersetzt nicht die Guardrails.

## Was seit dem 03.10.-Checkpoint neu verifiziert ist
- Telegram-/Privatmedien-Strecke wurde weiter gehärtet. Private Uploads bleiben privat; keine Social-Veröffentlichung allein durch Upload/Transkript/Preview.
- PR #371: private Telegram-Album-/Medien-Ingest-Basis auf main.
- PR #375: Telegram-Härtung; 25/25 relevante Telegram-Tests waren im damaligen Lauf grün.
- PR #377: realen Turkish-Rider-Fehler abgesichert: eine Freigabe wie `T1 posten` darf nicht einen alten pending Beitrag eines anderen Riders (konkret Toprak-Auswahl vs. alter Deniz-Inhalt) übernehmen.
- PR #378: zusätzliche Publisher-Dedupe-/Idempotenz-Schicht, Merge-Commit `897c5d0cce44dfe6f17da6783f85c15a35a9a26a`. Vier PR-CI-Stränge SUCCESS: Racing Priority/Turkish Five, Scheduled Publishing Queue, Instagram OG Image Test, Instagram False Success Hotfix Test.

## Publisher-/Dedupe-Invarianten ab diesem Stand
1. Turkish-Rider-Postaktionen werden gegen den Besitzer-Chat fail-closed geprüft.
2. Dieselbe Telegram-Update-ID darf eine Turkish-Postaktion nicht zweimal ausführen.
3. Dedupe arbeitet nicht nur mit identischem Caption-Text, sondern zusätzlich mit kanonischer Artikelquelle, Story-Key und Event-Fingerprint.
4. Tracking-Parameter bzw. eine umgeschriebene Caption machen denselben Artikel nicht zu einem neuen Publish-Kandidaten.
5. Legacy-`TR-HUMAN`-Migration ist an die Story/Quelle gebunden; gleicher Slot T1/T2 allein reicht nicht. Ein neuer Toprak-T1 darf keinen alten Deniz-T1-Block übernehmen.
6. Positive Control: zwei tatsächlich verschiedene Artikel bleiben publizierbar.
7. Keine Aussage, dass damit jede theoretisch mögliche zukünftige Doppelpost-Ursache ausgeschlossen ist; die identifizierten Fehlerwege sind regression-getestet.

## Blockstatus
### Block 7 — Audio / Untertitel / Stimme
Noch nicht vollständig abgenommen. Nächster Hauptschritt ist der belegbare private E2E-Pfad R2 → Container-Warm-up → ASR/Whisper → Transkript → Telegram/Dashboard. DE/TR-Ausgabe, Untertitel und die bereits autorisierte Voice-/Avatar-Strecke folgen erst nach sicherem privaten Datenpfad. Keine private Sprachdatei veröffentlichen.

### Block 8 — Dashboard / Medien
Synthetischer FFmpeg → privates R2 → Revision/Preview → Telegram wurde bereits nachgewiesen. Dashboard-Player/Upload sind grundsätzlich vorhanden. Vollständige Endabnahme für automatisches Neurendern, Ergebnisanzeige und Besitzer-Praxistest bleibt im Gesamt-E2E zu bestätigen.

### Block 9 — Jobeingang / Telegram / Publisher
Upload/Mikrofon/Chat/Telegram/Dashboard werden zur universellen Auftragseingangsschicht ausgebaut. Publisher-Handoff ist jetzt um #377/#378 gehärtet. Kein echter Social-Test ohne konkrete Beitragsfreigabe. Private Aufträge bleiben privat.

## Heutige Reihenfolge nach diesem Backup
1. Block 7 privaten R2→Warm-up→Whisper/ASR→Transkript-E2E nachweisen.
2. Telegram und Dashboard an diesen Ergebnisweg anbinden und Rückgabe prüfen.
3. Block 7/8/9 gemeinsame Endabnahme mit synthetischem bzw. ausdrücklich freigegebenem privaten Testmaterial; kein Social-Livepost.
4. Danach KI-Zentrale/Provider weiter ausbauen. Qwen PR #374 bleibt bis dahin separater Draft und darf die Hauptlinie nicht blockieren.
5. Danach Agenten-/Produktionsleiter-/Ressourcenmanager-Feinschliff und universelle Werkstatt für Recherche, Reise, Tarife, Shopping und private Medienaufträge.

## Werkzeug-/Kostenregeln
- FFmpeg FIRST; Remotion ergänzend nur bei Bedarf.
- R2 = privater Speicher, nicht Rechenserver.
- OpenChatCut PAUSED, SupoClip PAUSED, OmniRoute/Omniroot/OmniHut PAUSED.
- Selora nur Backup-Idee; nicht integrieren.
- Free-first. Keine zusätzlichen Kosten ohne ausdrückliche Freigabe.
- Private Medien niemals eigenständig publizieren.
- Keine Social-Veröffentlichung ohne konkrete Human Authority.

## Wiederanlauf
1. Aktuellen `main`, offene PRs und Actions erneut prüfen.
2. `PROJECT_GUARDRAILS.md`, diesen Handover und den zugehörigen Snapshot lesen.
3. Prüfen, ob `main` mindestens den gesicherten Code-HEAD `897c5d0…` enthält.
4. Keine alte OpenChatCut-/OmniRoute-Roadmap als aktuellen Plan behandeln.
5. Keine bereits gemergten #377/#378-Fixes doppelt bauen.
