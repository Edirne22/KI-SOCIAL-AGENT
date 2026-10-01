# SNAPSHOT 2026-10-01 – KI-ZENTRALE LIVE / OPENCHATCUT BLOCK 6 OFFEN – V5
**Verifiziert:** 01.10.2026 ca. 18:40 MESZ (16:40 UTC). **main:** `efad1f9e7000864a20fc235b5b235be4760d2e06`. **Code-Backup:** `backup/2026-10-01-ai-central-live-v5`.

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN
Vor Arbeiten: `PROJECT_GUARDRAILS.md` lesen. Die Regeln gelten unabhängig vom Snapshot und können von ihm nicht überschrieben werden. Keine Tests umgehen, keine erfundenen LIVE-Erfolge, Merge nur mit ausdrücklicher Nutzerfreigabe.

## Bestätigt LIVE
- Früher: Factory Blocks 1–9 als Softwarebasis auf main; Cloudflare R2 privat, ImageRouter→R2 und Agnes-Video→R2 separat LIVE nachgewiesen.
- Heute: nach Bülents ausdrücklicher Freigabe PR-Kette #277→#281→#282→#283→#284→#285 in main gemergt, letzter Merge `efad1f9e7000864a20fc235b5b235be4760d2e06`.
- Dashboard `https://edirne22-ai-central-dashboard.butupeli.workers.dev` im zweiten Live-Deploy `36890679417` erfolgreich bereitgestellt; zwei notwendige Worker-Secrets gesetzt. Readiness `36889977605`: 6/6 benötigte Secret-Namen vorhanden; erstes Deployment `36890152420` wegen zu kurzem Dashboard-Passwort vor Deployment gescheitert, anschließend behoben.
- Erster realer **Nutzer**-Dashboard-E2E: Task `a5f61ccc-ecac-4824-a489-d1598d1385ab`, GitHub `36891798853` SUCCESS, 2 Free-Rollen ANSWER, privater R2-Bericht archiviert und über reale Handy-Dashboard-Oberfläche angezeigt.
- Zweiter realer OpenChatCut-Evidenzauftrag: `cf413efc-5593-4ef1-9d0c-ce74cfa908d0`, `36892856318` Workflow SUCCESS, Research UNAVAILABLE/ERROR, Challenge ANSWER, Nutzer sah R2-Bericht. Kein Root-Cause-Beweis.
- Separat früher Claude via OpenRouter und OpenCode real verifiziert; **noch nicht** als produktiver Dashboard-Start verdrahtet, ggf. kostenpflichtig.

## Nicht als LIVE annehmen
- Aktueller Free-Workflow zwei Rollen über einen `openrouter/free`-Router; zwei verschiedene tatsächlich eingesetzte Modelle **nicht nachgewiesen**.
- Dashboard-GitHub-Run-Anzeige zeigte `Keine aktuellen Läufe im Suchfenster` trotz echter Erfolgsruns, ungeklärter Anzeige-/Suchfilter.
- Telegram End-to-End-Senden/Starten im produktiven Betrieb, Audio-Transkription, dauerhafte OpenCode-/OmniRoute-Installation, direkter ChatGPT→private R2-Taskabruf, Claude-Dashboard-Dispatch, Excel-Originalbearbeitung nicht vollständig nachgewiesen.
- OpenChatCut/SupoClip bleiben ungeprüft in der vollen Live-Medienkette.

## OpenChatCut/BLOCK 6 P1
Cloudflare Worker-only Health 200, Container-MCP mehrfach HTTP 000/14s; CF running ≠ App bereit. Gepinntes OpenChatCut-Image direkt unter Docker: 5/6 MCP-Sessions PASS, 1 TypeError FAIL, Prozess danach running/EXIT0/OOM false; Vite-Fehler `Failed to load url /@fs/src/main.tsx` beobachtet, Ursache offen. Isolierte MCP-SDK-Tests reproduzierten Sessionverlust nicht. Bisher kein realer voller Import/Edit/Headless-Render/R2/SHA/ffprobe/7-15-30s-Abnahmenachweis.
Offen #271, darauf gestapelt #278 mit bereits implementierter interner Loopback-Diagnose und Worker-only Test; Tests/Contract auf #278 erfolgreich, Live-Diagnose noch ausstehend. Weitere #268, #272–274, #276 gesondert abgleichen.
**Nächster Schritt:** vorhandenen #278-Diagnoseweg gegen aktuelle Instanz/CI prüfen, keine Doppelentwicklung; gegebenenfalls sichere Live-Loopback-Probe ohne OpenChatCut-Container-Image-Rollout, reale Root Cause ermitteln und erst danach fixen.

## Backup / weitere Details
Diese Datei ist ein kompakter neuer Einstieg. **Vollständige verbindliche Übergabe:** `docs/PROJEKT_UEBERGABE_5_2026-10-01.md`; ältere Snapshot-Historie bleibt unverändert. Verifizierte Original-Übergabe Nr. 4 wurde im zugänglichen aktuellen Repository/Library nicht eindeutig gefunden; V5 führt belegte ältere und neue Übergaben zusammen, nicht behauptete Originaldatei 4 kopiert.
