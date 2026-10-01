# 01.10.2026 – OpenChatCut #67 / Übergabe während Live-Deploy

**Zeitpunkt:** ca. 12:14 MESZ (10:14 UTC). **Status ist eingefroren:** sofort Live-GitHub prüfen, nicht als aktuellen Laufzustand behandeln.

## Sofortige Fortsetzung
Repo `Edirne22/KI-SOCIAL-AGENT`. **Run #67** `36847153610`: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36847153610
Letzter Live-Check: Contract **SUCCESS**, Deploy **IN_PROGRESS** genau bei `Deploy Worker, container and runtime secrets atomically` (`wrangler deploy --secrets-file`). Container-Readiness (drei aufeinanderfolgende MCP-Initialize HTTP 200 + protocolVersion) und Live-Acceptance noch nicht gestartet. Bitte zuerst Run/Jobs/Logs neu abfragen; keine zweite Dispatch parallel.

## PR / technische Änderungen
PR #271 https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/271, Branch `fix/openchatcut-cloudflare-lifecycle-readiness`, zuletzt OPEN und mergeable. Prüf-HEAD und Deploy-Commit `3324349b8f0c91218cdb4b2dbaab1efea1824ebf`. PR CI OpenChatCut #65 (`36845827738`): **SUCCESS** (TypeScript, Wrangler dry-run, Upstream-Pin). Block 6 #50 (`36845827677`): **SUCCESS**. PR-Checks allein deployen absichtlich NICHT.
- `feeadd029...`: native Cloudflare-Readiness `requiredPorts=[5199]`, `startAndWaitForPorts` vor Proxy; Lifecycle-Logs Start/Stop/Error, `sleepAfter="5m"`.
- `c592ce85...`: expliziter TS-Check; nach echtem Deploy 3 MCP-Readiness-Probes nacheinander, dann Live-Acceptance; PR-Acceptance gegen alte Installation entfernt.
- `9def7824...`: tsconfig ergänzt.
- `3324349b...`: Cloudflare ENV-TS-Typen repariert. #65 hat TS und Wrangler bestanden.

## Zentrale Evidenz/Fehlerhistorie
Altes System: `The container is not listening in the TCP address 10.0.0.1:5199`. Auch bei später funktionierendem MCP `status/create_project/target_project` scheiterte `begin_edit_session` zeitweise sofort oder nach 60s mit `Container suddenly disconnected, try again`. Recovery scheiterte sekundär an nicht exposed `list_edit_sessions`, neue Sitzung braucht ToolSearch/load_skill. Alte PR #269 **ohne Merge geschlossen** (experimentelle Diagnostik). Isolierter Warm-up PR #270 in main gemergt: erster Kontakt HTTP 500, zweiter erfolgreich nach insgesamt ~20s. Früherer Produktions-Deploy hing schon in `wrangler deploy` VOR Warm-up. Portbereitschaft beweist nicht Stabilität bei echten Edits/Render. Aktuelles Deploy #67 muss neuen Code zuerst tatsächlich installieren.

## Projekt-Kanon
`MASTER-SNAPSHOT.md`, `PROJECT_GUARDRAILS.md`, `AGENTS.md` und `snapshots/SNAPSHOT_2026-09-30_OPENCHATCUT_BLOCK6_LIVE_CANDIDATE.md` lesen; ältere Stände nicht blind übernehmen. Nach bestätigtem 30.09.-Stand Factory Blocks **1–9 auf main**, R2 und ImageRouter→R2 sowie Agnes Video→R2 LIVE; **OpenChatCut und SupoClip NICHT LIVE**. R2 dauerhaftes Lager, Container temporäre Werkbank. Ziel: SOURCE → SUPOCLIP → OPENCHATCUT → FFMPEG → R2 → GOLDEN TABLET → BÜLENT → PUBLISHER. Human-Freigabe bleibt ausschließlich bei Bülent. Kein künstliches PASS, kein Bypass, kein Auto-Merge.

## Aktuelle verbindliche Arbeitsregeln
`/BLOCKRUN`: Fehler → Joblog → Root Cause → kleiner sicherer Fix → CI → nächster Test; keine Geheimnisse offenlegen, nichts auf main ohne Abnahme mergen. Vor Einbau einer neuen Maschine/API/CLI zuerst **offizielle Dokumentation und genaue Version** vollständig untersuchen: Prereqs, Lifecycle, Port-Readiness, Ressourcen, Persistenz, Rechte, Deployment/Rollout, Logging und Recovery. Diese Maschinen-Regel noch in Guardrails konsistent festschreiben. Reevaluiere ehemals verworfene **SupoClip**-Integration später mit korrigierter Infrastruktur. Jules wurde als unabhängiger Zweitentwickler/Auditor für PR #271 angefragt; noch keine Ergebnisse voraussetzen. Keine parallelen unkoordinierten Änderungen auf demselben Branch.

## Beweisziel
Nach #67 mindestens echten Containerstart, stabiles MCP, `begin_edit_session`, Input/Timeline/Edit/Commit, Headless-Render MP4, ffprobe, privates R2 Upload/Download, SHA-Identität, Negativtests und 7/15/30s einschließlich Captions/Audio abnehmen, bevor OpenChatCut als LIVE gilt.

## Benutzerkommunikation
Nutzer Bülent wünscht Deutsch, direkte selbstständige Fehlerarbeit und sichtbare mobile Statusanzeige `Bestanden/Läuft/Wartet/Rot`. Zwischen aktiven Toolabfragen Status erneuern, aber niemals automatische Hintergrundüberwachung einer bestehenden Chat-Nachricht vortäuschen. Manuelle GitHub-Actions-Dispatch nur verlangen, wenn Connector nachweislich keine Dispatch-Aktion besitzt.

**Nächster Schritt:** Jetzt Run #67 neu abfragen und bei Rot exakte Logs untersuchen; bei grün Readiness und echte Edit-Session verfolgen.

## NACHTRAG 01.10.2026 – Ergebnis des echten Deploy #67 (ca. 10:26 UTC)

**Run 36847153610 vollständig beendet:** contract SUCCESS; deploy SUCCESS; live-acceptance FAILURE. Damit wurde der Readiness-Code von PR #271 tatsächlich deployed. Keinen weiteren Blind-Deploy starten.

- Wrangler Worker-Upload um ca. 10:11:53 UTC; Containeranwendung erfolgreich aktualisiert ca. 10:15:32 UTC.
- Post-Deploy MCP-Readiness: Versuch 1 HTTP 200; 2 HTTP 500; 3/4 HTTP 200; 5 HTTP 500; 6/7/8 HTTP 200. Drei aufeinanderfolgende gültige Initialize-Antworten um 10:17:02 UTC bestätigt.
- Live-Acceptance gegen die deployed Version um 10:17:48: geschützte Health 200 und MCP-Raw-Initialize 200. MCP Client connect um 10:17:50 erfolgreich, Session-ID erhalten; allererster Werkzeugaufruf `openchatcut_status` um 10:17:51 fehlgeschlagen mit `MCP session not found or expired` (JSON-RPC code -32001).
- Medienimport/Edit/Render/R2 wurden NICHT erreicht. Readiness bestätigt nur kurzzeitige Erreichbarkeit, keine Session-Stabilität. Wiederholte HTTP 500 während Probe sind wesentlich.
- Nächste Analyse: korreliere Session-ID/Container-Instanz und Lifecycle-Telemetrie zwischen erfolgreichem MCP Initialize und unmittelbar folgendem Tools-Call; prüfe OpenChatCut-MCP-Session-Store, Proxy-Routing und Cloudflare-Container-Neustart/Rollout. Keine Root Cause ohne weitere Evidenz behaupten.
- Jules als unabhängigen Reviewer mit genau diesen neuen Daten aktualisieren. Nachweise aus GitHub: Run https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36847153610 (Deploy-Job 110320684191; Live-Job 110323189461).

## NACHTRAG – Session-Fehler auf Codeebene lokalisiert (nach #67)

Im exakt gepinnten Upstream `0xsline/OpenChatCut@d1af1ade45521e8ed9a5be09e3acad823f269453`, Datei `server/external-agent/mcp.ts`, steht die exakte Fehlermeldung `MCP session not found or expired`. `handleMcpRequest` liest Header `mcp-session-id`, prüft die pro Node-Prozess im RAM gehaltene `const sessions = new Map<string, McpSession>()` und gibt bei fehlendem Eintrag HTTP 404 / JSON-RPC -32001 zurück. Session wird bei `onsessioninitialized` eingetragen, bei `onclose`/Eviction verworfen. Das beweist **NICHT**, dass der Container neu gestartet wurde: Prozessrestart, Session-Close oder andere Session-Routing-Probleme sind getrennt zu untersuchen.

In unserem Worker `infra/openchatcut-cloudflare/src/index.ts` steht die Fehlermeldung nicht. Dort sind `workerBootId` und `workerStartedAt` **modulweite Variablen des Cloudflare-Worker-Isolates**. Sie belegen keinen Startzeitpunkt des OpenChatCut-Containerprozesses und dürfen nicht als Crash-Indiz interpretiert werden.

Konfiguration `wrangler.jsonc`: `instance_type = standard-2`, `max_instances = 1`, EU-Regionsvorgaben. 6-GiB-RAM-Klasse, aber OOM ohne Lifecycle-Exit-Evidenz nicht behaupten. Nächste harte Diagnose: Cloudflare Container-Lifecycle-Logs (onStart/onStop/onError und Exit-Grund) im erweiterten Zeitfenster **10:16–10:21 UTC** mit Upstream-MCP-Session-Init/Close korrelieren; keine Vergrößerung oder blinden Retries.

## Jules – verbindliche Diagnose-Ergänzung (01.10.2026)

**Zeitfenster:** Cloudflare-Lifecycle- und Anwendungslogs **10:16–10:21 UTC** erfassen, einschließlich aller Zwischenstarts, onStart/onStop/onError, Exit-Codes, Rollout-/Proxy-Fehler und MCP-Sitzungsereignisse. Zeitangaben korrekt interpretieren: 10:17:48 UTC war die *geschützte Health-Anfrage* im GitHub-Live-Test und **kein nachgewiesener Containerstart**. MCP-Client-Sitzung um ca. 10:17:50 UTC eingerichtet, erster Werkzeugaufruf um 10:17:51 UTC mit -32001/Session not found gescheitert.

**Beide Code-Fundstellen dokumentieren:** Unser Worker `infra/openchatcut-cloudflare/src/index.ts` (PR #271 / SHA 3324349b...) enthält die Zeichenfolge `MCP session not found or expired` **nicht**. Im exakt gepinnten Upstream `0xsline/OpenChatCut@d1af1ade45521e8ed9a5be09e3acad823f269453` liegt sie in `server/external-agent/mcp.ts`, innerhalb `handleMcpRequest` nach `pruneMcpSessions(now)` und fehlgeschlagenem `sessions.get(sessionId)`. Dort ist `sessions` eine Prozess-RAM-`Map`; `onsessioninitialized` registriert Sessions, `transport.onclose` / `pruneMcpSessions` können sie entfernen. Jules soll genau diese Mechanismen und Session-ID-Protokollierung gegen Logs prüfen, keine vorzeitige Ursache festlegen.

**Boot-ID-Herkunft:** `workerBootId` wird in `workerIdentity()` in unserem Cloudflare Worker-Modul (`src/index.ts`) erstellt, nicht im Containerprozess. Die Boot-ID ist daher kein Nachweis für einen Container-Restart.

**Änderungsstopp:** keine weitere Runtime-Änderung, Instanzvergrößerung oder zusätzlichen Retries vor gesichteter Lifecycle-/Session-Evidenz.

## NACHTRAG – Unabhängige Hypothese GET-Stream / SDK und verifizierte Upstream-Limits

Exakt gepinnter Upstream `server/external-agent/mcp.ts`: `MCP_SESSION_IDLE_LIMIT_MS = 60 * 60 * 1000` (60 Minuten), `MCP_SESSION_COUNT_LIMIT = 64`. `transport.onclose` ruft unmittelbar `forgetSession(session, 'cancelled', ...)` auf; `forgetSession` entfernt die Session aus der Prozess-`Map` und storniert Editor-Calls. Bei bloß ca. 1 Sekunde zwischen MCP-Connect und `status` und etwa zehn erzeugten Probe-Sessions erklären Leerlauf-/Anzahl-Limits den beobachteten Verlust nicht plausibel.

Neue **unbestätigte** Hypothese: SDK eröffnet nach Initialize eventuell langlebigen GET-Eventstream, und ein Proxy-/Stream-Abbruch könnte den Upstream-Transport schließen und `onclose` auslösen. Vor Schlussfolgerung SDK-/Upstream-Stream-Close-Verhalten prüfen, zusätzlich Lifecycle-Logs im Fenster 10:16–10:21 UTC auswerten.

Gezielter diagnostischer Vergleich erst nach Ressourcen-/Logabgleich: begrenzte Roh-MCP-Folge (`initialize` → `tools/call openchatcut_status` mit derselben Session-ID, ohne SDK/GET) versus SDK-Folge mit GET-Stream; jeweils Status, Response-Header und redigierten Fehlerbody insbesondere bei HTTP 500 aufzeichnen. Nur synthetische Status-Calls, keine Medienjobs, keine Secrets oder Session-IDs in öffentlichen Logs veröffentlichen. Niemals allein durch Retry-Erfolg als LIVE bewerten.

## NACHTRAG – PR #272 isolierter MCP-Vergleich, 01.10.2026 10:44 UTC

**Draft-PR:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/272. **Diagnoselauf:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/36850902796, Job 110332042155, erwartungsgemäß FAILURE, weil echte Verbindungsfehler nachgewiesen wurden. **Kein Runtime-/Cloudflare-Deploy.** Sechs Paare rohes HTTP MCP (initialize → initialized notification → tools/call status, ohne SDK/GET) gegen MCP-SDK mit connect/call/close.

**Messwerte:** roh 3 PASS / 3 FAIL, SDK 1 PASS / 5 FAIL. Rohversuche 3–5 lieferten HTTP 404 / JSON-RPC -32001 `MCP session not found or expired`. SDK-Versuche 2,3,4,6 verloren ebenfalls Session. SDK-Versuch 5: `Error proxying request to container: The container is not listening in the TCP address 10.0.0.1:5199`. Die spezifische Hypothese, **allein** SDK-GET-Stream-Abbruch verursache den Fehler, ist dadurch widerlegt. Raw-Transport ist selbst instabil; SDK kann zusätzlichen Einfluss haben, aber nicht einzige Ursache sein. Der kurzzeitige Port-Ausfall macht Lifecycle-/Prozess-/Proxy-Stabilität zum vordringlichen Untersuchungsziel, ohne Neustart oder OOM bereits zu beweisen.

**Nächster harter Beweis:** Cloudflare-Lifecycle- und Anwendungslogs auch rund um **10:44:12–10:44:37 UTC** des isolierten Vergleichs erfassen, zusätzlich zum bisherigen **10:16–10:21 UTC**. onStart/onStop/onError/Exit-Grund und Proxy-Fehler zeitlich korrelieren. Bis dahin keine Blindfixes, keine zusätzlichen Retries, keine Vergrößerung und kein LIVE-Label.
