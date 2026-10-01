# EDİRNE 22 – PROJEKTÜBERGABE NR. 5 / GESAMT-BACKUP
**Zeitpunkt:** 01.10.2026, ca. 18:40 MESZ / 16:40 UTC  
**Repository:** Edirne22/KI-SOCIAL-AGENT  
**Verifizierter Ausgangspunkt main:** `efad1f9e7000864a20fc235b5b235be4760d2e06`  
**Unveränderlicher Code-Wiederherstellungspunkt:** `backup/2026-10-01-ai-central-live-v5` (ab genau diesem main-Commit angelegt)  
**Dokumentationszweig:** `feature/project-handover-v5-2026-10-01`  
**Wahrheitsgrenze:** Zeitpunktdokument; bei Wiederaufnahme zuerst aktuellen GitHub-HEAD, PRs, Runs und Deploymentstatus neu prüfen.

## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN

Vor Arbeiten am Repository zuerst vollständig lesen:

**`PROJECT_GUARDRAILS.md`**

Diese Regeln gelten unabhängig vom aktuellen Entwicklungsstand und dürfen durch diese Projektübergabe nicht überschrieben werden. Außerdem `MASTER-SNAPSHOT.md`, `AGENTS.md`, den gleichzeitigen aktuellen V5-Snapshot und die älteren Medien-/OpenChatCut-Snapshots lesen. Bei Widersprüchen: aktuellen Code, jüngste überprüfbare Logbelege und bestätigte Entscheidungen heranziehen, nichts stillschweigend überschreiben.

**Keine Auto-Merges, keine automatischen Veröffentlichungen, keine Secrets/Privatdaten in öffentliches GitHub, keine erfundenen erfolgreichen Tests.** /BLOCKRUN bedeutet: Status melden → im autorisierten Scope weiterarbeiten; ROT → echte Logs → Root Cause → kleinster sicherer Fix → Tests/Red Team → CI; Merge nur mit ausdrücklicher Freigabe von Bülent. Für echte externe Toolabnahme reicht ein grüner Offline-Test nicht. Niemals eine fortlaufende Hintergrundüberwachung behaupten, wenn keine echte Automation aktiv ist.

## 1. Übergabehistorie und Grundlage von Nr. 5

Bülent verlangt eine fortlaufende Übergabe Nr. 5, die die früheren Projektübergaben 1–4 weiterführt. **WICHTIGE ARCHIVLÜCKE:** Der exakte Dateiinhalt und Pfad einer ausdrücklich „Projektübergabe Nr. 4“ benannten Datei ließ sich im aktuellen `main` sowie in der zugänglichen ChatGPT-Bibliothek nicht eindeutig verifizieren. Es wäre unwahr, eine wortgetreue Fortschreibung dieser Datei zu behaupten. V5 baut deshalb belegbar auf folgenden tatsächlich zugänglichen Dokumenten/Protokollen auf:
- `MASTER-SNAPSHOT.md` und `PROJECT_GUARDRAILS.md` (verbindlicher Projektindex und Regeln).
- `snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md` (vollständiger Factory-/Media-Meilenstein).
- `snapshots/SNAPSHOT_2026-09-30_OPENCHATCUT_BLOCK6_LIVE_CANDIDATE.md` und `snapshots/SNAPSHOT_2026-10-01_OPENCHATCUT_DEPLOY_67_HANDOVER.md` (OpenChatCut-, Container- und KI-Zentrale-Untersuchungen).
- `docs/OPENCHATCUT_BLOCK6_QUICK_HANDOVER.md` (historische Kurzübergabe).
- Ehemalige vollständige Chat-Übergabe in ChatGPT-Dateibibliothek `EDIRNE22_HANDOVER_2026-10-01_1014.md` (Stand 12:14 MESZ, nachfolgende Angaben überholt).
- Echt verifizierte GitHub-PR-, Commit- und Workflow-Daten vom 01.10.2026 und Bülents anschließende tatsächliche Dashboard-Live-Abnahme.

Wenn die Originaldatei Nr. 4 später auffindbar wird, Inhalt gegen V5 abgleichen, nicht unbesehen ersetzen.

## 2. Kanonische Factory-/Racing-Architektur

Factory Blocks 1–9 wurden früher bereits auf `main` gemergt. Das umfasst Core, Persistenz, Discovery, evidenzbasierte Redaktion, Creative/Writing, Media-Verträge, AV-Verträge, Final QM/Golden Tablet und Control Center/Publisher-Bridge; dies bedeutet **nicht**, dass sämtliche externen Medienmaschinen bereits LIVE funktionieren.

Kanonische Kette: `INPUT → ORCHESTRATOR → DISCOVERY/NEWSROOM → CREATIVE → MEDIA → AV → FINAL QM/GOLDEN TABLET → HUMAN AUTHORITY → PUBLISHER`.
Medienziel: `SOURCE / GENERATED MEDIA → SUPOCLIP/ggf. geprüfter Ersatz → OPENCHATCUT → FFMPEG/EXPORT → privates R2 → GOLDEN TABLET → BÜLENT → PUBLISHER`.

Zuvor real LIVE verifiziert: privates Cloudflare R2, ImageRouter → R2 und Agnes Video → R2. OpenChatCut und SupoClip **nicht** vollständig LIVE abgenommen. Bereits bestehender echter Legacy-Meta-Publisher ist vom noch teils simulierten neuen Factory-Bridge-Contract zu unterscheiden. Turkish-Rider- und Racing-Fakten-QM, Source-Fact-Provenance, DEGRADed-PASS ohne Wahrheitsschranken-Umgehung und Human Authority bleiben bindend. Bülent entscheidet endgültig Ändern / Verwerfen / Posten; keine automatische Veröffentlichung ohne Freigabe.

R2 = privates dauerhaftes Medien-/Task-/Berichtsarchiv, **keine Rechnerlaufzeit**. GitHub = Code, Tests, temporäre Actions-Runner; Cloudflare Worker = privates Dashboard; Cloudflare Container = derzeit experimentelle OpenChatCut-Werkbank. Privat-Laptop ist **kein** Teil der produktiven Zentrale. Späterer x86-VPS nur nach realen Benchmarks und ausdrücklicher Kosten-/Bestellfreigabe.

## 3. Heutiger echter KI-Zentrale-Meilenstein (01.10., verifiziert)

Nach ausdrücklicher Nutzerfreigabe wurde die vorher gestapelte PR-Kette **in exakter Reihenfolge** auf main gemergt:
- #277 KI-Control-Plane / GitHub-Runner und R2: Merge-Commit `b8a4cea0e7084cc41b0be4c3edb86661968ae770`.
- #281 mobiles gemeinsames Dashboard/Telegram R2-Inbox: `872e371cf26a09a71cc3dbef50b9c3071f82b639`.
- #282 OpenCode, Claude-only-Lane, Tools/Skills: `66369ccdc22f3f3ae05057bbb00fe1cb425b51a1`.
- #283 futuristisches mobiles KI-Cockpit: `59e602c142148a8830ca8bae0b3a3a84b5d3e54a`.
- #284 kontrollierte R2-Auftragsvalidierung: `0fdeff03676c0b32cafcd3827db185eee4c45a32`.
- #285 expliziter kostenloser Dashboard → GitHub → R2-Berichtspfad: `efad1f9e7000864a20fc235b5b235be4760d2e06` (bei Sicherung aktuelles main).
PRs waren vor Merge überprüft, jeweils konfliktfrei; relevante PR-CI erfolgreich, manuelle Live-Prüfungen bewusst teils übersprungen, statt fiktiv als PASS etikettiert.

**Neue vom Nutzer ausschließlich in GitHub hinterlegte Secrets:** `AI_DASHBOARD_TOKEN` (Dashboard-Passwort, mindestens 24 Zeichen) und `AI_GITHUB_DISPATCH_TOKEN` (repo-spezifischer Fine-Grained Actions Read/Write Token). Niemals Werte in Dokumentation kopieren! Fine-Grained-Token laut Nutzer-Screenshot mit Ablauf **30.12.2026**; echte ChatGPT-Erinnerung zur Erneuerungsprüfung am **28.12.2026 vormittags** eingerichtet. Token-Erneuerung bedeutet Secret `AI_GITHUB_DISPATCH_TOKEN` aktualisieren und Auth-/Dispatch-Test durchführen.

Readiness-Run `36889977605` SUCCESS: beide neuen Tokens sowie Cloudflare API, Account, R2-Bucket und OpenRouter-Key `CONFIGURED`; der nur informatorische zusätzliche Repo-Variablencheck `FREE_GATE=DISABLED`, da für tatsächlichen Deploy/Runner die zuvor echt geprüfte `openrouter/free`-Route bereits im Code gesondert hart gebunden ist. *Dieses historische Flag nicht mit Freigabe bezahlter Anbieter verwechseln.*

Erster Dashboard-Deploy `36890152420` FAILURE **vor dem Deploy**: erstes Dashboard-Passwort kürzer als 24 Zeichen. Nutzer korrigierte das Secret; zweiter Run `36890679417` **SUCCESS**, Wrangler Deploy, Worker-/R2-Bindung und Installation beider benötigten Worker-Secrets in Logs bestätigt. Bereitgestellte Adresse:
`https://edirne22-ai-central-dashboard.butupeli.workers.dev`
Nutzer meldete grünen Punkt `R2 verbunden`, tatsächlich autorisierten Zugang und gespeicherte Web-Aufträge. Dashboard ist privat API-geschützt; Worker-URL an sich nicht mit allseitiger Cloudflare-Access-Zugangsschranke gleichsetzen.

**Echter End-to-End-Test aus realem Dashboard:**
- erster Web-Auftrag ID `a5f61ccc-ecac-4824-a489-d1598d1385ab`, manuell angefordert;
- GitHub-Run `36891798853` SUCCESS, `research=ANSWER`, `challenge=ANSWER`, beide über `openrouter/free`; vollständiger privater R2-Bericht archiviert;
- Nutzer zeigte Bericht tatsächlich auf Handy im Dashboard, Status `PENDING_REVIEW`. Somit **Dashboard-Eingabe → private R2-Inbox → manuelle Freigabe → GitHub Free-Runner → privater R2-Bericht → Dashboard-Berichtsanzeige LIVE bewiesen.**

**Zweiter realer OpenChatCut-Diagnoseauftrag:**
- Web-Task-ID `cf413efc-5593-4ef1-9d0c-ce74cfa908d0`;
- GitHub-Run `36892856318` SUCCESS als Workflow; **research=UNAVAILABLE / openrouter/free ERROR**, **challenge=ANSWER**; privater R2-Bericht `PENDING_REVIEW` vom Nutzer eingesehen und Text in Chat übergeben.
- KI-Vorschläge waren **Advisory, kein Root-Cause-Beweis**. Die Behauptung „HTTP 000 beweist Netzwerkfehler“ ist falsch; externe Netzwerkprobe würde den internen Container-Loopback nicht trennscharf erklären. Interne Loopback-Diagnose war bereits in #278 umgesetzt: keine Doppelentwicklung.
- `PENDING_REVIEW` ist menschliche Prüfpflicht, nicht automatischer Abschluss oder Freigabe.

**Grenzen der neuen Zentrale:** Der kostenlose automatische Pilot benutzt **nur die feste Route `openrouter/free`**, derzeit zwei unabhängige Rollen-Prompts, **nicht nachgewiesen zwei tatsächlich unterschiedliche Modelle**. Claude über OpenRouter/OpenCode wurde separat real getestet (Runs `36868165522` und `36868533302`), kann kostenpflichtig sein und ist **nicht** mit dem Dashboard-Auswahlknopf produktiv verdrahtet. OpenCode/OmniRoute CLI wurden auf **kurzlebigem GitHub-Runner** installiert/geprüft (Run `36873304821`), nicht dauerhaft auf R2. PDF/DOCX/XLSX-Neuerzeugung und isolierte FFmpeg-Smokes früher erfolgreich, unverfälschtes Editieren hochgeladener Excel-Dateien noch nicht abgenommen. Audioaufnahme speichert Datei, transkribiert/dispatcht nicht. Telegram hat gemeinsame R2-Inbox und vorbereiteten expliziten `/zentrale starten <id>`-Pfad; echter Telegram-End-to-End-Live-Beweis zum Sicherungszeitpunkt **nicht erhoben**. Die Live-GitHub-Laufanzeige zeigte dem Nutzer `Keine aktuellen Läufe im Suchfenster` trotz erfolgreicher Runs: Suchfenster/Filter/Abfrage prüfen; nicht als repariert melden. Öffentlicher GitHub-Code enthält keine privaten Task-/Modellausgaben; diese liegen nur in privatem R2. Aktueller ChatGPT-GitHub-Connector kann Repo/PR/Actions prüfen, jedoch keinen nachgewiesenen direkten privaten R2-Volltextzugriff behaupten.

## 4. Block 6/OpenChatCut – getrennte belegte Diagnoselage

Aus dem früheren OpenChatCut-Live-Stand:
- geschützter Cloudflare Worker `/_factory/health` antwortete HTTP 200; mehrere authentifizierte MCP-Anfragen zu Containerroute dagegen HTTP 000/14s Timeout.
- Cloudflare-Instanzverwaltung meldete OpenChatCut `running`, 1 Instanz, Version 11 (Messung 01.10. 12:01 UTC), **kein Beweis** funktionierender Vite-Anwendung/Port 5199.
- direkte Docker-Isolation des gleichen gepinnten Upstream-Dockerfiles: echter MCP-Initialize erreichbar, sechs vollständige rohe Sessions **5 PASS / 1 FAIL**, ein `TypeError` im Fehlerfall. Container blieb running, `EXIT=0`, `OOM=false` bei diesem Experiment. Wiederholte Vite-Warmup-Meldung `Failed to load url /@fs/src/main.tsx` vorhanden, aber ursächlicher Zusammenhang nicht bewiesen.
- reine MCP-SDK-Simulation inkl. GET-SSE-Abbruch reproduzierte Sessionverlust nicht. Cloudflare-Tail lieferte trotz korrigiertem Parser keine verwertbaren Lifecycle-Logs, also **kein** gemessener Crash-/OOM-Nachweis.
- frühere echte Session schaffte `openchatcut_status → create_project → target_project`, scheiterte bei `begin_edit_session` mit `Container suddenly disconnected`. Diese Funktion und volle Render-/Import-/R2-Abnahme fehlen.

**Offene, nicht fälschlich als gemergt/LIVE darstellen:**
- #271 `fix/openchatcut-cloudflare-lifecycle-readiness`, HEAD `3324349b8f0c91218cdb4b2dbaab1efea1824ebf`, Basis main.
- #278 `diag/openchatcut-in-container-port-inspection`, HEAD `73756825c8cd167e5997e24514e2c11e1170120b`, gestapelt auf #271; Offline-`test` und `contract` erfolgreich, Live-`deploy` und `live-acceptance` übersprungen/noch nicht durchgeführt.
- weitere offene Diagnose-PRs #272, #273, #274, #276 und Block-6-#268 separat prüfen; **keinen** parallelen Branch oder doppelten Fix aus alter Übergabe starten.
#278 implementiert geschützten `/_factory/container-diag`-Endpoint, `ctx.container.exec` mit fest eingebautem Node-Skript für **interne Loopback-GET-Probe** an `127.0.0.1:5199/api/external-mcp/mcp`, no arbitrary model input; Abfrage soll schlafenden Container nicht absichtlich starten. Zu #278 gehören `occ-worker-loopback-live.yml` (geplanter Worker-only Deploy mit `--containers-rollout=none` und Vergleich der Instanzidentität) sowie `occ-rpc-error-snapshot.yml`. **Vor jedem Einsatz** aktuellen Cloudflare-Zustand, Security, Abhängigkeit #271 und CI prüfen; es liegt weder explizite Merge-Freigabe für #278 noch eine bestätigte Live-Abnahme vor. Externer KI-Review empfahl eine ähnliche interne Healthprobe, nicht nochmal implementieren.

**Noch nötiger echter Medien-Staffellauf:** Port/Container/App-Root-Cause nachweisen → fehlerarme MCP-Sitzungen/Start → `create/target/begin_edit_session` → echter Input-R2-Import → Timeline/Edit/Commit → native Headless-MP4-Ausgabe → ffprobe Codec/Auflösung/Dauer → privater R2-Upload/Download und SHA-256 → Negative/Timeout/Restart/Resume → 720×1280/7s, 1080×1920/15s, 1080×1920/30s, Captions/Audio → erst danach OpenChatCut-Adapter LIVE. Anschließend SupoClip/ggf. kontrolliert evaluierten Ersatz und vollständige Factory-Staffel. Keine VPS-Ausgaben ohne Freigabe.

## 5. Aktuelle Arbeitsreihenfolge / nächster ausführbarer Schritt

1. Vor jedem neuen Eingriff HEAD, laufende GitHub-Actions und relevante PR-Basen prüfen; Übergabe-V5-Dokumentation von technischem Runtime-Branch getrennt halten.
2. Nutzer soll **keinen dritten gleichen KI-Analyseauftrag** bezahlen oder starten; zweiter kostenloser Lauf brachte eine verwertbare einzelne Antwort, aber keine trennscharfe Root Cause.
3. #278/#271 und vorhandene Workflows inklusive Auth, Wiederaufwachen-Risiko, Logs und Versionen kontrollieren. Entscheidung: zuerst verlässliche interne Loopback-Diagnose ohne unbeabsichtigten OpenChatCut-Image-Rollout, soweit sichere technische Voraussetzungen und erforderliche Nutzerfreigabe vorliegen.
4. Ergebnis gegen direkten Docker-Repro (TypeError.cause + Vite-Warmup) und Worker-vs-Container-Timeout vergleichen. Nur nach evidenzbasierter Diagnose minimalen Fix, Tests/Regression/Security/Staffellauf.
5. Separat Dashboard GitHub-Run-Filter prüfen und kostenlose Modellrolle-Fehler transparent messen; weder separaten Claude-Modus noch Telegram-Automatik als bereits LIVE behaupten.

## 6. Datensicherheit, Kosten, Wiederaufnahme

- Öffentliche GitHub-Repo-Dateien nur **Dokumentation/Code/öffentliche Run-IDs**, keine Auftragsvolltexte/Modelldialoge/Secret-Werte/privaten R2-Dateien.
- Tokens nur über GitHub-Secrets/Cloudflare Worker; Ablauf GitHub Dispatch Token laut Screenshot 30.12.2026, Erinnerungsprüfung 28.12.2026.
- Nur geprüfte zero-price-Free-Lane automatisch; bezahlte Claude-/Bild-/Video-Modelle ausschließlich nach ausdrücklicher Entscheidung mit Budgetkontrolle.
- Backup-Branch schützt den Repository-Zustand exakt bei Sicherung; dies **ist keine Kopie privater R2-Medien, Cloudflare-Secrets oder aller externen Dienstkonten**. Separates Storage-Backup nur mit gesicherter Freigabe und geeigneten Datenschutzmaßnahmen.
- Bei Wiederaufnahme: `PROJECT_GUARDRAILS.md` → `MASTER-SNAPSHOT.md` → diese V5 → Snapshot V5 → neuesten OpenChatCut-Snapshot → HEAD/PRs/Actions live lesen → exakt ab realem jüngsten Zustand fortsetzen; keine parallelen Branches und keine doppelten Deploys.
