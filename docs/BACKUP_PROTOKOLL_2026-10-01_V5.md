# EDİRNE22 – BACKUP- UND WIEDERHERSTELLUNGSPROTOKOLL NR. 5
**Sicherungszeit:** 01.10.2026, ca. 18:40 MESZ (16:40 UTC)  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Verifizierter main zum Start:** `efad1f9e7000864a20fc235b5b235be4760d2e06`

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN
Vor Arbeiten zuerst `PROJECT_GUARDRAILS.md` lesen. Dieses Protokoll ersetzt keine Regeln. Keine automatischen Merges, keine Veröffentlichung ohne Bülents Freigabe, keine privaten Daten in einem öffentlichen GitHub-Repository.

## 1. Umfang und Sicherungsorte
- **Git-Code/Repository-Zustand:** `backup/2026-10-01-ai-central-live-v5`, vom obigen exakten main-Commit abgezweigt. Enthält den vollständigen zu diesem Git-Commit verfolgten Dateistand **inklusive früherer Snapshots, Code und Workflow-Konfigurationen**. NICHT technisch gesperrt: Branch nicht verschieben, umbenennen, überschreiben oder löschen.
- **Neue fortschreibende Dokumentation auf separatem PR-Branch `feature/project-handover-v5-2026-10-01`:** `docs/PROJEKT_UEBERGABE_5_2026-10-01.md`, `snapshots/SNAPSHOT_2026-10-01_AI_CENTRAL_LIVE_BLOCK6_HANDOVER_V5.md`, dieses Backup-Protokoll, Ergänzung des `MASTER-SNAPSHOT.md`-Index. Diese neuen Dokumente sind **nicht Bestandteil des eingefrorenen Codebranches**, sondern zunächst eigenständig über den Dokumentations-PR versioniert; erst nach ausdrücklich genehmigtem Merge gehören sie zu main.
- **Historie:** ältere Snapshots und Guardrails im Codebackup erhalten; ChatGPT-Bibliotheksdatei `EDIRNE22_HANDOVER_2026-10-01_1014.md` als weitere ältere externe Zeitpunktquelle auffindbar.
- **Bekannte Lücke:** Der Wortlaut/Dateipfad der vom Nutzer erwähnten früheren Übergabe Nr. 4 war im zugänglichen aktuellen GitHub-Tree und der indizierten ChatGPT-Library nicht eindeutig nachweisbar. V5 ist deshalb eine vollständig neu belegte konsolidierte Übergabe, keine unbestätigte wortgetreue Kopie von Nr. 4. Nach künftigem Auffinden Nr. 4 additiv abgleichen.

## 2. Was ausdrücklich NICHT gesichert ist
Dieser GitHub-Branch ist **kein** Cloudflare-R2-Objektbackup, kein Export der privaten R2-Inbox/Medien oder privat gespeicherten KI-Berichte, kein Cloudflare-Worker-Rollback und keine Kopie der GitHub-Secrets, OpenRouter-Schlüssel oder Tokenwerte. Public-Repo: diese privaten Daten bewusst nicht exportieren. Ein echter externer Disaster-Recovery-Backupplan mit Verschlüsselung/Zugriffskontrolle erfordert gesonderte Planung und gegebenenfalls Freigabe; nicht als erledigt markieren.

## 3. Bei Chatwechsel oder Abbruch zwingend
1. `PROJECT_GUARDRAILS.md`, `MASTER-SNAPSHOT.md`, `docs/PROJEKT_UEBERGABE_5_2026-10-01.md`, V5-Snapshot und die vorherigen Block-6-/OpenChatCut-Dokumente lesen.
2. GitHub `main` HEAD, alle offenen PRs/Basen, laufende GitHub-Actions und Dashboard-Deployment **neu** abfragen. Vorliegende Run-IDs sind Zeitpunktbelege, keine ewige Liveüberwachung.
3. Bereits gemergte KI-Zentrale-PRs #277, #281–#285 **nicht** neu erstellen; aktuellen main vergleichen. Bestehende offenen OpenChatCut-PRs #271/#278 und #268/#272–274/#276 vor jeder Änderung auswerten.
4. Dashboard-Verbindung und realen Nutzer-E2E `36891798853` nicht mit vollständiger OpenChatCut-Live-Abnahme verwechseln. Zweiter E2E `36892856318` hatte 1/2 Antworten.
5. Bei nötigem Rollback niemals blind main/Container überschreiben: Backup-Commit und tatsächliche neuere legitime Commits vergleichen, sicherheitsspezifische Regression/CI durchführen und vor Merge/Deploy explizit Bülents Zustimmung einholen.

## 4. Nächster nach Sicherung offener technischer Schritt
Bereits vorhandene, nicht gemergte #278-Loopback-Diagnose gegen #271 und aktuellen Cloudflare-Containerzustand prüfen. Möglichst Worker-only, ohne OpenChatCut-Image-Rollout, mit Instanz-Vorher/Nachhervergleich und echten Logbelegen arbeiten. Wenn nicht beweisbar: keine Root-Cause-Behauptung. Danach vollständigen Block-6-End-to-End-Medienweg nach Guardrails abnehmen. Separat den fehlenden Github-Run-Anzeigeeintrag im Dashboard und die fehlgeschlagene erste Modellrolle untersuchen.

## 5. Zugriff und Ablauf
- Dashboard: `https://edirne22-ai-central-dashboard.butupeli.workers.dev`.
- **Keine** Secret-Werte im Repo, Backup oder Chat.
- `AI_GITHUB_DISPATCH_TOKEN` laut Nutzerscreenshot Ablauf 30.12.2026; bestätigte ChatGPT-Erinnerung 28.12.2026 vormittags.
- Sämtliche Angaben dieses Protokolls beziehen sich auf den oben angegebenen Zeitpunkt; spätere Runs/Branches können den Zustand verändert haben.
