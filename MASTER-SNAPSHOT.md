# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

> **/BLOCKRUN-FORTSETZUNG BLOCK8 DASHBOARD 02.10.2026 (AKTUELL, PR #315/#316):** Nach Wiederaufnahme aktuelle Main-/Automations-Arbeit geprüft und PR310–314 bereits als gemergt erkannt, deshalb nicht dupliziert. [PR #315](https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/315) `a728ace5afa2f6d2f43c2826ab10c0463758075c` gemergt, beide Dashboard-CIs `37001496776`/`37001496783` SUCCESS, Cloudflare Live Deploy `37001585698` SUCCESS. `previewManifest` prüft jetzt bei JEDEM R2-Listen-/Videoabruf zusätzlich den autoritativen geteilten canonical `FACTORY-CANONICAL-R2-JOB-V1` auf job_id, `ready_for_human`, Revision, unveränderte private Video-ID/URI/SHA/Größe/MIME und exakten Caption-Text. Veraltete/gelöschte/verworfene oder unlesbare canonical Jobs verbergen auch dann ihre Preview, wenn ein alter `preview-state`-Pointer versehentlich noch existiert. Ältere technische Fixtures ohne canonical Speicherung verschwinden absichtlich; neuere PR310-geprüfte Fixtures haben canonical R2 und bleiben regulär bis zur 2h-TTL abrufbar. [PR #316](https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/316) `7dc3ba992fc52aa0538be2893e755f775239bc47` gemergt, beide Dashboard-CIs `37001795974`/`37001795995` SUCCESS, Cloudflare Deploy `37001874539` SUCCESS. Neuer authentifizierter read-only `GET /api/reviews` listet tatsächlich privat in R2 persistierte PENDING-/APPLIED-Anträge nach geladenem Dashboard neu, nur gültige Actor-/Revision-/Status-Records. Live-Konsole zeigt 'Deine gespeicherten Entscheidungen' > 'Entscheidungen prüfen'. Kein Browser-LocalStorage für Auth/Review und kein Post-Button. **NÄCHSTER BLOCK8-NACHWEIS (echte Human Authority, NO POST):** Bülent selbst wählt einen noch gültigen, in canonical R2 persistierten TECHNISCHEN Testvideoeintrag (aus PR310 neuer Preview `b7cf110e-ddf4-4d72-bd25-5c9cc6a74251`, Job `e828bf49-cf1d-4cf3-b238-6b35c23239af`, falls seine 2h-TTL noch nicht abgelaufen ist) und bestätigt im echten Dashboard 'Änderung anfordern' mit eindeutigem Testwunsch. Danach GitHub block8-dashboard-review-consumer Run und tatsächliche R2-Review-Status-ACK prüfen; nur dann Block8 Change UI als wirklich human-live abgenommen erklären. Eine technische Fixture NIEMALS posten. Nach TTL neue separate PR-/Workflow-getriggerte sichere isolierte technische Preview generieren, keine falsche Live-Abnahme. BLOCK9: PR309 shared R2 Ledger, PR312 Facebook Adapter und PR313 real isolierter R2-Live-CAS bereits gemergt/testbestätigt, aber keine echte Meta-Publikation ohne dedizierte verifizierte Mensch-Freigabe. INSTAGRAM signed private gateway, echte redaktionelle Quellen-/Rechtebelege und finaler Human-POST-Workflow weiterhin offen.

> **BLOCK 8 SHARED R2 IfMatch REALER NEGATIV-/POSITIVTEST (02.10.2026 13:03:57 MESZ):** PR #314 gemergt `47ba2a37260fdfdf8cce236afa0204d52962206a`. Isolierter tatsächlicher Cloudflare-S3-R2-Test für die identischen IfMatch-CAS-Semantiken des canonical ProductionJob Store auf `ai-central/v1/canonical-cas-smoke/<uuid>.json`: Pull-Request-Offline-Regressions-Run `36998828296` PASS; derselbe Main-Run `36998878261` offline + echter privater R2 Job SUCCESS mit Log `BLOCK8_PRIVATE_R2_IFMATCH_LIVE_PASS concurrent_winner=1 stale_writer_blocked=1 saved_version=2 isolated_objects_cleaned=true real_human_actions=0 real_platform_requests=0`. Ein paralleler veralteter Writer wurde blockiert, readback valide, Testdatei entfernt; weder echter Canonical-Job noch Bülent-Entscheidung/Meta API war beteiligt. Zusammen mit Block9 echtem isoliertem R2 IfNoneMatch-Smoke Run `36998551805` sind beide bedingten R2-Speichermechanismen praktisch belegt. **Nicht mit kompletter Block8-Nutzerfreigabe oder echtem Block9-Social-Publishing verwechseln**. Die restlichen Human-POST-, echte redaktionelle Source-/Media-Rights-Provenienz- und Instagram-privat-gateway Aufgaben bleiben gesperrt, bis fachlich und praktisch nachgewiesen.

> **BLOCK 8/9 /BLOCKRUN FORTSCHRITT, 02.10.2026 ~13:00 MESZ (AKTUELLER TECHNISCHER STAND):** Block 6 ist durch Bülents persönlich erfolgreich abgespieltes 15s-Testvideo im echten Cloudflare-Dashboard praktisch für den technischen privaten Preview-Pfad abgenommen (nicht die gesamte redaktionelle Publishing-Kette). Block 8 PR #307 (Dashboard Änderung-/Verwerfen-Wunsch-UI, kein Post-Button) gemergt `b8615c8`, CI grün; Cloudflare Deploy Run `36996433970` SUCCESS. PR #308 (canonical SQLite CAS review-applier inklusive Neustart/Idempotenz) gemergt `d5c8041`; nach sicherem requests-Dependency-Fix Run `36996650558` SUCCESS. PR #310 (shared CAS private R2 canonical ProductionJob store, echte FFmpeg→R2-Preview-Registrierung persistiert canonical ready job vor Vorschau) gemergt `aaa76b8`; offline Runs `36997133864` und `36997133835` SUCCESS; neuer echter main FFmpeg→private R2 canonical-job+Video-Index Run `36997296132` beide Jobs SUCCESS mit Preview `b7cf110e-ddf4-4d72-bd25-5c9cc6a74251`, Job `e828bf49-cf1d-4cf3-b238-6b35c23239af`, rev 1, 15 Sekunden Audio/Video. PR #311 (Dashboard-Button→auth+canonical verified R2 media→CAS review-state request→event-driven existing GitHub dispatch→R2 canonical Factory HumanDecisionService CHANGE/DISCARD→conditional R2 ACK→read-only PENDING-vs-APPLIED UI) gemergt `4ac5da5`, alle drei PR Runs `36997689655`, `36997689854`, `36997689697` SUCCESS; echtes Cloudflare Dashboard Deployment Run `36997755582` SUCCESS auf bereits bestehender geschützter workers.dev-Adresse. **Bülent hat den neuen CHANGE/DISCARD-Workflow noch NICHT persönlich mit einem Klick und einem konkreten echten Auftrag abgenommen; ein bestandener Fake-R2-Test belegt das nicht.** Kein POST-Button, der Server gibt POST 409 zurück, bis echte editorial und persönliche Freigabeverknüpfung abgenommen ist.
>
> **BLOCK 9:** PR #309 shared private R2 S3 conditional `PutObject IfNoneMatch=*` first-writer-Claim, immutable receipts, no blind retry nach unsicherem Timeout, fake-R2-Race und Crash-Test gemergt `7e01e4f`, CI `36996885299` SUCCESS. PR #312 Adapter für vorhandenen `facebook_publish.post_video_to_facebook()` hinter Canonical-Job-Reload, unverändertem Manifest, explizit menschlichem per-post Approval-Metadatum, Fakten/Human-Writing/Medienrechte-Evidence, unabhängigem privatem R2-Video-Download und atomarem R2-Publish-Ledger gemergt `fbe987c`, offline keine Meta-Anfragen, CI `36998074716` SUCCESS; INSTAGRAM REELS weiterhin absichtlich gesperrt, da noch kein nachweislich gültiger kurzlebiger Meta-abrufbarer privater Medien-Gateway vorhanden ist. **PR #313** isolierter echter R2-only Claim-Test gemergt `9152e3de1d5ebd562747e6fd3557d90b2a1f855f`; PR Checks `36998411917` und `36998411696` SUCCESS; **Echter Main Cloudflare R2 Test** Run `36998551805`, offline und live Jobs SUCCESS, Log `BLOCK9_PRIVATE_R2_ATOMIC_SMOKE_PASS parallel_first_writer=1 blocked_duplicate=1 restart_receipt=verified private_test_only=true real_platform_requests=0` 02.10.2026 11:00:39Z. Alles unter isoliertem `ai-central/v1/publish-ledger-smoke/` Namespace, kein echter Nutzerauftrag, keine Meta- oder IG-Anfrage. Dies belegt S3-R2-Race und Receipt, NICHT echte Social-Veröffentlichung. **Noch offen für volle Block8/9-Endabnahme:** tatsächliche User-CLICK→GitHub→canonical Job→R2 ACK in realem System (nur mit Bülents tatsächlicher Änderung/Verwerfen-Entscheidung), echte redaktionelle Fakten-/Rechte-/QM-Approval-Attestierung vor manifestgebundenem persönlichen POST-Button (synthetische Fixture niemals veröffentlichen), nachweisliche Publish-Workflow-Anbindung mit kontrolliertem Meta-Provider und anschließendem belegtem Receipt, Instagram Meta-reachable begrenzter privater Mediengateway. Keine neuen Kosten, keine Social-Posts ohne spezifische Human Authority, keine Simulation als Live-End-to-End.

> **BLOCK 6 PRIVATE DASHBOARD-VIDEOVORSCHAU – HUMAN PLAYBACK PASS (02.10.2026 ca. 11:32 MESZ):** Bülent hat am eigenen Android-Handy den im echten Cloudflare KI-Central-Dashboard authentifiziert abrufbaren R2-Testfilm **ausgewählt und erfolgreich abgespielt**; Screenshot zeigt `Das Video wurde privat geprüft und kann abgespielt werden` sowie Job `95a98381-5ae7-4fa1-b26a-bfe6a273deb4`, Revision 1, `EDIRNE 22 – TECHNISCHES TESTVIDEO (NICHT VERÖFFENTLICHEN)` und sichtbaren Player. Dieser Benutzertest ergänzt den echten Cloudflare-Deploy-SUCCESS Run `36989328537` und den Factory→FFmpeg→privates R2→Preview-Index-SUCCESS Run `36989328481`, registrierte Preview-ID `271fe40e-b038-4f7d-bd6c-48b7bba301fe`, 15 Sekunden Audio+Video; PR #305 gemergt `e08fa72b1e804fc4b68047613f1b71a4dbfc9c58`. **Abgenommen ist der technische synthetische Block-6-Dashboard-Wiedergabepfad; NICHT der vollständige redaktionelle User-Input→echtes finales QM→Bülent-Human-Authority→Publisher-E2E.** Block 8 benötigt noch tatsächliche revisions- und identitätsgebundene Web-Aktionen Ändern/Verwerfen/Posten (PR #303 Preview-Revoke/TTL bereits gemergt) und sicheres dauerhaftes Job-State-Handoff. Block 9 braucht reale bestehende Publisher-Anbindung und zu vorhandener Runtime passende atomare dauerhafte Idempotenz, niemals ohne konkrete menschliche Postfreigabe real veröffentlichen. Keine Wiederholung desselben bereits bestandenen technischen Testfilms ohne Grund.

> **BLOCK 6 DASHBOARD-PLAYER: CODE UND CI GEMERGT (02.10.2026, nach Mitternacht MESZ):** [PR #302](https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/302), Merge `446e3f1eff40f900c11e40f789fc3d0a23a0b4f6`. Der bestehende KI-Central-Dashboard-Worker besitzt nun **Code** für authentifizierte private `GET /api/previews`-Liste, `GET /api/preview-video` mit unabhängiger tatsächlicher SHA-256-/Größen-/MIME-Prüfung und 32-MiB-MVP-Grenze; Web-UI zeigt einen Video-Player mit Bearer-geschütztem Fetch/Blob statt öffentlicher R2-URL; `content_factory_dashboard_preview.py` kann einen realen FinalQM-PASS/`R2Storage`-Job per Block-8-Verified-Gate im R2-Preview-Index registrieren. PR-Head `19606cfbf...`: Run `36932648649` **SUCCESS** (Python, privater Medien-/Golden-Tablet-Vertrag, Node-Video-Sicherheit/alte Dashboard-Regression, SOURCE-FACT); Shared Inbox Run `36932648707` **SUCCESS**. Dies ist **nicht** die LIVE-Dashboard-Abnahme: `ai-central-dashboard-deploy.yml` wird derzeit nur manuell ausgelöst, Dashboard-Live-Deployment und tatsächlich vom FFmpeg-Lauf gefüllter Preview-Index noch offen; alter/revidierter Preview-Index muss vor Human-Approval revokations-/aktuell-revisionssicher invalidiert werden. Player zeigt bewusst **keine** Live-Post-/Ändern-/Verwerfen-Funktionen. Weiter ohne aktiven Telegram-Bot: bestehende Factory→FFmpeg→R2-Strecke an R2-Preview-Registrierung anschließen, realen Player-Deployment-/Playback-Test durchführen, danach sicheres Block-8-Manifest-/Human-Authority-UI und Block-9-Publisher-Handoff. Älteren Branch `feature/block6-private-media-preview` nicht als Dashboard-Player ausgeben (nur separater Telegram-Helper, veraltet).

> **AKTUELLE NACHTSCHICHT BLOCK 6/8/9 (01.10.2026):** Bülent hat die autonome Entwicklung und grün geprüfte PR-Merges für Block 8 und 9 ausdrücklich freigegeben; **Block 7 bis morgen früh pausiert** (Bülents persönliche Stimme noch NICHT aufgenommen/geklont). Block 8: [PR #300](https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/300) auf main gemergt, Merge `8706f4a8d0c7cc8f45df5683f9f73b4d3935312a`. Neuer opt-in `content_factory_golden_media.py`-Gate: tatsächlicher privater MediaStorage-Download, unabhängig verifizierter SHA/Größe/Medientyp, QC/Revision/Manifest vor `READY_FOR_HUMAN`; 12 echte Offline-Positiv-/Negativtests + bestehende Block-8-/SOURCE-FACT-CI auf korrigiertem Head `8609f421...` **SUCCESS** (Run `36931009041`). Noch **keine** tatsächliche Telegram-/Dashboard-Abspielvorschau oder eingesetzter Live-R2-End-to-End-Gate. Block 9: [PR #301](https://github.com/Edirne22/KI-SOCIAL-AGENT/pull/301) auf main gemergt, Merge `a46b607d92b3c0790799bfb36f34a2a830919176`. Neuer optionaler `content_factory_publish_ledger.py` mit atomarer POSIX-Dateireservierung/Receipt, blockiert unklare Publisher-Timeouts über Neustarts und unterstützt nur verifizierte manuelle Reconciliation; 14 Offline-Tests + Block-9-/Publisher-No-Work-/SOURCE-FACT-CI **SUCCESS** Run `36931199974`. **WICHTIGE GRENZE:** POSIX-Dateiledger taugt nur für tatsächlich gemeinsames dauerhaftes Volume, **nicht** für ephemere GitHub-Actions-Runner oder verteilte Cloudflare-Worker/R2-Instanzen; Live-Betrieb benötigt nachgewiesene atomare gemeinsame Persistence und echte Adapterkopplung. Keine echte Plattformpublikation getestet/ausgelöst. Als Nächstes Block-6-Preview-Branch auf tatsächlichen HEAD prüfen, vollständigen privaten R2→abspielbaren Telegram-/Dashboard-Preview→Golden-Tablet→Human Authority-Stafellauf, danach Block-9-Durable-Backend/Altpublisher. Keine Werkzeuganschaffungen, kein autonomes Publizieren.


> **BLOCK 8/9 VORARBEIT (01.10.2026):** `docs/BLOCK8_9_VORABPRUEFUNG_2026-10-01.md` – geprüfter main-Code für Golden Tablet, gemeinsame Web-/Telegram-Steuerung, bestehende Publisher, R2/Worker-Kompatibilitätsgrenzen, fehlender privater Preview, Auth-Kopplung und persistente Publish-Idempotenz; keine neuen Toolkosten oder unbestätigten LIVE-Claims.

> **EINZIGER WERKZEUG-/ALTERNATIVENINDEX:** `docs/TOOL_INDEX.md`. Vor Toolauswahl und bei Toolfehler **immer dort beginnen**, nicht separat IDEA_POOL, FREE_TOOLS oder datierte Screenshot-Radare durchsuchen. Diese älteren Dateien sind Quellen/Archiv. Die Fallback-Matrix im zentralen Index gilt zusammen mit `PROJECT_GUARDRAILS.md` §14. Für neuen Chat oder `/BLOCKRUN` zuerst Index lesen und aktuelle E2E-Belege neu prüfen.

 > **HISTORISCHER FALLBACK-EINTRAG:** Die frühere Liste `docs/TOOL_RADAR_2026-10-01_27_SCREENSHOTS.md` wurde in den zentralen `docs/TOOL_INDEX.md` überführt. Ab sofort nur den neuen Index für die Werkzeugauswahl verwenden. Nach **Nutzerfunktion**, nicht Toolnamen, Ersatz auswählen; `RESEARCH_ONLY` nie als `LIVE` deklarieren. Siehe Guardrails §14.

> **NEU: Tool-Radar aus 27 Screenshots (01.10.2026):** `docs/TOOL_RADAR_2026-10-01_27_SCREENSHOTS.md` enthält Quellenlinks, Dopplungen, Lizenz-/Kostenwarnungen und gezielte Kandidaten (Pixelle-Video, Agent-Reach, Crawl4AI, Codebase-Memory-MCP, OpenMontage nur als Architektur-Referenz). Nur Recherche: keine Installation, kein LIVE-Nachweis, keine Prioritätsumkehr gegenüber der offenen privaten Preview. 

> **VERBINDLICHE FUNKTIONS-/WERKZEUG-ENTSCHEIDUNG (01.10.2026):** Vor jeder neuen Sitzung und jedem /BLOCKRUN `PROJECT_GUARDRAILS.md` Abschnitt 14 lesen. Bülents Nutzerziel ist *Sprachauftrag oder Medien-Upload rein → autonom die passenden austauschbaren Maschinen wählen → fakten-/mediengeprüftes Ergebnis zur menschlichen Freigabe*, nicht das Durchsetzen bestimmter Tools. Wiederholt problematische externe Werkzeuge nach wenigen begrenzten, unterschiedlichen Diagnoseversuchen dokumentieren und durch nachweislich funktionierende Alternativen ersetzen; keine Endlosschleifen. **Block 6:** FFmpeg als getesteter unabhängiger Render-/Caption-/Audio-Weg; Remotion ergänzend, Chopify zunächst nur zu prüfender Clip-Kandidat; OpenChatCut/SupoClip derzeit keine Abschlussvoraussetzung und ggf. später auf VPS untersuchen. R2 ist privates Medienlager, kein Rechencontainer; OmniRoute bleibt pausiert. PR #298 und #299 sind auf main gemergt; #299 lokaler Factory-FFmpeg-Integrationstest und Block-6-/Agnes-/ImageRouter-PR-Prüfungen PASS. **Nachgelagerter main-Push-Live-Test Factory→FFmpeg→privates R2 ist erfolgreich abgeschlossen:** Bülents GitHub-Actions-Screenshot vom 01.10.2026, 22:39 MESZ, zeigt für #299/f823329 sowohl `factory-offline` (48s) als auch `factory-live-private-r2` (1m17s) grün, Gesamt 2m12s. Das beweist den beschriebenen Testpfad, jedoch noch keinen vollständigen Spracheingang/Upload→privaten Telegram-/Dashboard-Preview→Human-Approval-Staffellauf; separate detaillierte Run-Logs waren mangels Run-ID nicht selbst gelesen. Ältere untenstehende SupoClip→OpenChatCut-Roadmaps sind **historisch und nicht mehr verbindliche Ausführungsreihenfolge**.


> **AKTUELLER NEUER PROJEKT-INDEX V6 (01.10.2026, ca. 20:18 MESZ):** Neue Bülent-Vision „autonomes KI-Unternehmen“ und genauer Restart: `docs/PROJEKT_UEBERGABE_6_2026-10-01_KI_UNTERNEHMEN.md`. Kompakter Stand: `snapshots/SNAPSHOT_2026-10-01_KI_UNTERNEHMEN_PRE_STEP1_V6.md`; Sicherung: `docs/BACKUP_PROTOKOLL_2026-10-01_V6.md`; Code-Backup bei `e1ebc471f22b8ad1512ac42dd30080478590413c`: `backup/2026-10-01-ai-central-vision-pre-stage2-v6`. V5-Vollübergabe liegt noch in offenem DRAFT-PR #286 (nicht main). PR #287 wurde gemergt; Live-Lauf #36903543954: NVIDIA Nemotron+Kimi beantworteten Aufgaben, OpenRouter-Gegenprüfung nicht; separater OmniRoute-Test schlug fehl und OmniRoute ist zurückgestellt. Bülent hat **Schritt 1** gestartet: NVIDIA/Gemini/Groq als tatsächliches kostenkontrolliertes Team in bestehende Dashboard/Telegram/R2-Kette bringen; danach Produktionsleiter/Ressourcenmanager, Block 6, gemeinsamer Deep-Research/Dauerbetrieb. Bei Wiederaufnahme GitHub-HEAD/PRs/Actions neu prüfen und `PROJECT_GUARDRAILS.md` zuerst lesen. Diese Zeile ist Plan/Snapshot, KEINE Behauptung über noch nicht implementierte Funktionen.


**Stand:** 30.09.2026, ca. 22:49 Europe/Berlin  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`  
**Funktion dieser Datei:** zentraler Einstieg / Inhaltsverzeichnis für den aktuellen Projektstand.

> Diese Datei ist bewusst kurz. Sie zeigt auf die verbindlichen Detail-Snapshots und Guardrails, statt alte Projektstände zu duplizieren.

**Live-Übergabe 01.10.2026 (neu):** `snapshots/SNAPSHOT_2026-10-01_OPENCHATCUT_DEPLOY_67_HANDOVER.md`. Dieser Zeitpunkt-Snapshot dokumentiert PR #271, den grünen Check #65 und den zum Erstellungszeitpunkt laufenden echten Deploy #67. Bei Wiederaufnahme **erst** aktuelle GitHub-Jobs/HEAD prüfen; den älteren 30.09.-Snapshot als Architektur-/Meilensteinbasis zusätzlich lesen.

## 1. Aktueller Einstieg

**Aktueller verbindlicher Arbeits-Snapshot:**

`snapshots/SNAPSHOT_2026-09-30_OPENCHATCUT_BLOCK6_LIVE_CANDIDATE.md`

Snapshot-Ausgangspunkt:
- Factory Blocks 1–9 gemergt.
- R2, ImageRouter → R2 und Agnes Video → R2 LIVE verifiziert.
- OpenChatCut Cloudflare-PoC deployed und als LIVE_CANDIDATE bis MCP/create_project/target_project real verifiziert.
- begin_edit_session zeigte einen Cloudflare-Disconnect; PR #259 diagnostiziert Restart/State-Verlust vs. Transportproblem fail-closed.
- aktueller Produktionslauf: 36773936472.
- OpenChatCut bleibt bis Import/Edit/Headless-Render/R2/SHA/ffprobe/7-15-30s-Caption-Audio-Abnahme NICHT LIVE.
- danach SupoClip LIVE integrieren und vollständige Video-Staffel testen.

**Verbindliche Guardrails:**

`PROJECT_GUARDRAILS.md`

Vor größeren Änderungen immer zuerst Guardrails + aktuellen Snapshot lesen.

## 2. Snapshot-Historie

### 30.09.2026 – LIVE Media / Cloud Workbench
`snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md`

Aktueller Stand nach Factory 1–9, R2 LIVE, ImageRouter LIVE und Agnes Video LIVE. Enthält außerdem Cloudflare-Container-/OpenChatCut-Strategie, SupoClip-Plan, Storage-/Lifecycle-Plan und P1/P2/P3-Roadmap.

### 30.09.2026 – Night Build
`snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_NIGHT_BUILD.md`

Historischer Übergabepunkt zu Beginn des Factory-Nachtbaus. Damals war Block 1 / PR #230 noch offen. Nicht mehr als aktueller Arbeitsstand verwenden.

### 29.09.2026 – Content Factory Milestone
`snapshots/SNAPSHOT_2026-09-29_CONTENT_FACTORY_MILESTONE.md`

Historischer Meilenstein nach Stabilisierung der Turkish-Rider-Human-Approval-/Publisher-Kette und vor dem großen Factory-Ausbau.

Backup:
`backup/2026-09-29-content-factory-milestone`

Dieser Backup-Branch bleibt eingefrorener Wiederherstellungspunkt.

## 3. Aktuelle Architektur in einem Blick

`INPUT → JOB/ORCHESTRATOR → DISCOVERY/NEWSROOM → CREATIVE → MEDIA → AV → FINAL QM/GOLDEN TABLET → HUMAN AUTHORITY → PUBLISHER`

Media-Zielweg:

`SOURCE / GENERATED MEDIA → SUPOCLIP → OPENCHATCUT → FFMPEG → R2 → GOLDEN TABLET → BÜLENT → PUBLISHER`

Aktuell real LIVE nachgewiesen:
- Cloudflare R2 Storage.
- ImageRouter → R2.
- Agnes Video → R2.

Noch nicht als LIVE abgenommen:
- SupoClip.
- OpenChatCut.

SIMULATED darf niemals als LIVE bezeichnet werden.

## 4. Infrastruktur-Merksatz

- **GitHub** = Baupläne, Code, CI.
- **Cloudflare Container / später VPS** = Werkbank und Maschinen.
- **Cloudflare R2** = dauerhaftes privates Medienlager.
- **Golden Tablet** = finale Human Preview.
- **Bülent** = finale Veröffentlichungsautorität.

Cloudflare Container dient zunächst als Beta-Messstand für OpenChatCut/FFmpeg. Ein späterer x86-VPS wird anhand real gemessener Qualität, Quantität, CPU/RAM/Disk, Renderzeit und Kosten dimensioniert.

## 5. Human Authority

Autonom erlaubt:
- Discovery.
- Recherche.
- Faktenprüfung.
- Creative.
- Medienproduktion.
- QM.

Veröffentlichung:
- Bülent entscheidet `Ändern / Verwerfen / Posten`.
- gültige Human-Freigabe darf von nachgelagerter KI nicht erneut vetoed werden.
- Änderung nach Approval macht die Freigabe ungültig.
- keine automatische Veröffentlichung ohne gültige Human Authority.

## 6. Wiederaufnahme-Anweisung

Bei neuer Session oder Projektübergabe:

1. `MASTER-SNAPSHOT.md` lesen.
2. `PROJECT_GUARDRAILS.md` lesen.
3. `snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md` vollständig lesen.
4. aktuellen `main` gegen den dort dokumentierten Stand prüfen.
5. bei P1 fortsetzen:
   - OpenChatCut Cloudflare-Container PoC.
   - echter OpenChatCutAdapter.
   - OpenChatCut → FFmpeg → R2 Live-Staffellauf.
   - SupoClip LiveAdapter.
   - Source → SupoClip → OpenChatCut → FFmpeg → R2 Gesamtstaffellauf.
   - sicherer Bild-/Video-Preview für Bülent.

Keine Tests umgehen, keine künstlichen PASS-Ergebnisse, keine QM-/Security-Gates deaktivieren und keine simulierten Provider als LIVE ausgeben.

## 7. Historischer Hinweis

Der frühere Inhalt dieser Datei dokumentierte detailliert den Racing-Stand vom 16.09.2026. Dieser Stand ist inzwischen durch zahlreiche spätere Commits, Übergaben und Snapshots überholt.

Historische Racing-Details bleiben in Git-Historie, Projektübergaben und älteren Snapshots nachvollziehbar. `MASTER-SNAPSHOT.md` dient ab jetzt als **lebender Projektindex zum jeweils aktuellen Snapshot** und nicht mehr als eingefrorene Vollkopie eines einzelnen Tages.
