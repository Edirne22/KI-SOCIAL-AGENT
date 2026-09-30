# SNAPSHOT – 2026-09-30 – OPENCHATCUT LIVE CANDIDATE / BLOCK 6

**Statuszeitpunkt:** 2026-09-30 ca. 22:49 Europe/Berlin  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Main beim Snapshot:** `e5db9ab93e6eeea721145fb4585613107379feb7`

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN

Vor Arbeiten am Repository zuerst lesen:

`PROJECT_GUARDRAILS.md`

Diese Regeln gelten unabhängig vom aktuellen Entwicklungsstand und dürfen durch diese Projektübergabe nicht überschrieben werden.

Aktiver Arbeitsmodus: `/BLOCKRUN`. Statusmeldung ist kein Stopp. ROT → Logs → Root Cause → Fix → neuer Lauf. Keine Tests, Security-, Fakten-, QM- oder Human-Authority-Gates abschwächen. SIMULATED niemals als LIVE bezeichnen.

## 1. Kanonischer Factory-Stand

Factory Blocks 1–9 sind auf main. LIVE verifiziert sind privates Cloudflare R2, ImageRouter → R2 und Agnes Video → R2. OpenChatCut und SupoClip sind noch nicht als LIVE abgenommen.

Zielweg:
`SOURCE / GENERATED MEDIA → SUPOCLIP → OPENCHATCUT → FFMPEG/EXPORT → R2 → GOLDEN TABLET → BÜLENT → PUBLISHER`

R2 bleibt dauerhaftes System of Record. Containerdisk bleibt temporäre Werkbank. Human Authority bleibt Bülent.

## 2. OpenChatCut – installierter Kandidat

Cloudflare-Container-PoC ist deployed unter dem geschützten Worker-Endpunkt. Upstream ist reproduzierbar auf `0xsline/OpenChatCut@d1af1ade45521e8ed9a5be09e3acad823f269453` gepinnt.

Container:
- Node 24 Bookworm
- FFmpeg
- Chromium
- Port 5199
- `sleepAfter = "5m"`
- Internet aktiviert
- Hardware-Encoding deaktiviert
- Render-Concurrency 50 %
- max. 1 aktiver Export
- exakter Vite-Host via `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS`
- Cloudflare Observability aktiviert

Bearer-Schutz ist aktiv. Unauthentifizierter und falscher Token werden abgewiesen. Geschützte Factory-Health meldet bewusst `LIVE_CANDIDATE`.

## 3. Belegte OpenChatCut-Fähigkeiten

Der gepinnte Upstream besitzt MCP `/api/external-mcp/mcp`, server-direct/offline Editing und eine native Headless-Exportpipeline. `occ render` und die Serverroute `/export` benutzen die echte Export-/Remotion-Pipeline; ein manuell verbundener Editor-Browser soll daher nicht Voraussetzung des Zielwegs sein.

Im echten Produktionslauf wurden bereits erfolgreich erreicht:
- geschützte Health
- MCP-Verbindung
- `openchatcut_status`
- `create_project`
- `target_project`
- Toolkatalog mit 44 Tools

Browsergebundene MCP-Tools werden nicht fälschlich als server-direct behandelt.

## 4. Aktuelles Finding

Run `36771860381`:
- contract PASS
- deploy PASS
- live-acceptance ROT

Fehler beim ersten `begin_edit_session({approvalMode:"auto"})`:
`Container suddenly disconnected, try again` / HTTP 500.

Der Fehler trat ca. 1–1,5 Sekunden nach `target_project` auf. Der 5-Minuten-Sleep erklärt diesen konkreten Zeitpunkt daher nicht direkt. Die Fehlermeldung allein beweist keinen Prozess-Crash; möglich sind Container-/Prozess-Neustart oder Transport-/Proxy-/TCP-Abbruch.

## 5. Aktuelle Diagnose

PR #259 wurde gemergt. Main: `e5db9ab93e6eeea721145fb4585613107379feb7`.

Der Acceptance-Test arbeitet weiterhin fail-closed. Bei einem Disconnect während `begin_edit_session`:
1. Fehler wird protokolliert.
2. geschützte Health wird erneut geprüft.
3. eine frische MCP-Verbindung wird aufgebaut.
4. `openchatcut_status` wird erneut gelesen.
5. exakt das unmittelbar vorher erzeugte `projectId` wird erneut mit `target_project` angesprochen.
6. Danach schlägt der Acceptance-Lauf weiterhin fehl, bis die Root Cause behoben ist.

Damit soll unterschieden werden:
- Projekt/State weg → Restart/State-Verlust untersuchen.
- Projekt weiterhin targetbar → Transport-/Proxy-Verbindungsproblem priorisieren.

Aktueller Produktionslauf: `36773936472`. Zum Snapshot-Zeitpunkt war das Deployment noch aktiv; Diagnose/Live-Acceptance folgt danach.

## 6. Noch NICHT abgenommen

OpenChatCut bleibt `LIVE_CANDIDATE`, bis mindestens bestanden:
- echter Input-Import
- editierbare Timeline
- Edit/Commit
- nativer Headless-Render
- echtes MP4
- ffprobe/Codec/Dauer/Auflösung
- privates R2 Upload/Download
- SHA-256-Identität
- Negative Controls
- 720×1280 / 7 s
- 1080×1920 / 15 s
- 1080×1920 / 30 s
- Captions + Audio
- relevante Retry/Crash/Resume/Handoff-Prüfungen

Erst danach darf der Factory-Port von SIMULATED auf echten OpenChatCut-LIVE-Adapter umgestellt werden.

## 7. Unmittelbare Fortsetzung

1. Run `36773936472` vollständig auswerten.
2. Bei ROT: Logs → Root Cause → Fix → neuer Produktionslauf.
3. Nach gelöstem Disconnect echten Importpfad R2 → OpenChatCut ergänzen.
4. Benchmark-Matrix inkl. Captions/Audio und Messwerten ausführen.
5. R2/SHA/ffprobe und Negativtests abschließen.
6. echten OpenChatCutAdapter anbinden.
7. vollständigen Factory-Staffellauf wiederholen.
8. Danach SupoClip LIVE und sicheren Golden-Tablet-/Preview-Weg fortsetzen.

## 8. Nicht verwechseln

Ein grüner Diagnose-Smoke macht OpenChatCut noch nicht LIVE. Ein erfolgreicher Render allein macht die vollständige Media-Kette noch nicht LIVE. Cloudflare Container ist Werkbank; R2 bleibt Lager. Secrets bleiben ausschließlich in GitHub Actions/Runtime-Konfiguration und gehören niemals in Snapshot oder Logs.
