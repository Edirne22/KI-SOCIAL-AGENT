# SNAPSHOT – 2026-09-30 – CONTENT FACTORY LIVE MEDIA & CLOUD WORKBENCH

Statuszeitpunkt: 2026-09-30 ca. 13:30 Europe/Berlin  
Repository: Edirne22/KI-SOCIAL-AGENT  
Main beim Snapshot: `99d3fecd204d4d0e577b9b2a9bb26ab9fb1f5da2`

## 1. Zweck und Anschluss an den letzten Snapshot

Dieser Snapshot setzt `snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_NIGHT_BUILD.md` nahtlos fort.

Der Night-Build-Snapshot entstand bei Main `1b0aef3...`, als Block 1 / PR #230 noch offen war. Seitdem wurde die Factory 1–9 fertig aufgebaut, gemergt und die Media-Schicht schrittweise von Contract/SIMULATED auf echte LIVE-Komponenten erweitert.

Der ältere Milestone `SNAPSHOT_2026-09-29_CONTENT_FACTORY_MILESTONE.md` und der Night-Build-Snapshot bleiben historische Wiederherstellungspunkte und werden nicht überschrieben.

Verbindlich bleiben `PROJECT_GUARDRAILS.md`, Human Authority und die DoD-/Staffellauf-Regeln. SIMULATED darf niemals als LIVE ausgegeben werden.

## 2. Seit dem Night-Build abgeschlossene Factory-Blöcke

Verifizierte Merge-Kette:
- #230 Factory Core Contracts – MERGED
- #232 Block-1 Combined-Main Acceptance – MERGED
- #233 Block 2 Persistence / Crash Recovery / Storage Contracts – MERGED
- #234 Block 3 Discovery + Editorial Scheduler – MERGED
- #235 Block 4 Evidence-bound Research + Facts Newsroom – MERGED
- #236 MiroFish Clean-Room Architecture Patterns – MERGED
- #237 Block 5 Creative Director + Bülent Writing – MERGED
- #238 Block 6 Media Production – MERGED
- #239 Block 7 Voice + Captions + Avatar/Motion Contracts – MERGED
- #240 Block 8 Final QM + Golden Tablet – MERGED
- #241 Block 9 Control Center + Publisher Bridge – MERGED
- #242 paralleler/staler Block-6-PR – CLOSED, NICHT gemergt
- #243 Agent-Reach Discovery Candidate – MERGED

Damit steht der kanonische Factory-Weg als eigene Architektur:
INPUT → JOB/ORCHESTRATOR → DISCOVERY/NEWSROOM → CREATIVE → MEDIA → AV → FINAL QM/GOLDEN TABLET → HUMAN AUTHORITY → PUBLISHER BRIDGE.

Human Authority bleibt unverändert: Bülent entscheidet Ändern / Verwerfen / Posten. Keine nachgelagerte KI darf eine gültige Human-Freigabe erneut vetoen.

## 3. Cloudflare R2 – vom Contract zum echten LIVE-Medienlager

### PR #244 / #245
- #244 `feat: add live Cloudflare R2 media storage` – MERGED
- #245 `fix: make R2 live smoke import repo modules` – MERGED

Bucket:
- `edirne22-content-factory`
- Region: Eastern Europe
- Public Access: AUS
- Bucket bleibt privat.

GitHub-Secrets/Config-Namen:
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT`

Keine Secret-Werte gehören in Repo, Snapshot, Chat oder Logs.

Implementiert:
- `R2Storage` als privater S3-kompatibler MediaStorageAdapter.
- SHA-256/Größen-/Bucket-/Key-Validierung.
- private `r2://bucket/key` MediaRefs.
- Upload + Resolve/Download + Integritätsprüfung.
- Lazy boto3.

LIVE-Nachweis:
GitHub Actions → GitHub Secrets → Cloudflare R2 → Upload → Download → SHA-256 PASS.

R2 ist ab jetzt das dauerhafte Medienlager/System of Record für wertvolle Medienartefakte, nicht die Render-Werkbank.

## 4. ImageRouter – erste echte LIVE-Medienmaschine

### PR #246
`feat: connect live ImageRouter to media factory` – MERGED.

`ImageRouterAdapter`:
- ExecutionTruth = LIVE.
- verwendet den bestehenden `image_router`.
- erzeugt IMAGE/CAROUSEL-Medien aus CreativeBrief/StoryBeat-Intent.
- speichert über MediaStorageAdapter/R2.
- revisions-/taskgebundene Provenance.
- immutable MediaRef + SHA-256.

### PR #247
`test: prove live ImageRouter to private R2 staffellauf` – MERGED.

Echter manueller LIVE-Staffellauf erfolgreich:
ImageRouter → Factory Adapter → privates R2 → Download → SHA-256 PASS.

Damit ist die Bildstrecke nicht mehr nur Contract/Simulation.

## 5. Agnes Video – zweite echte LIVE-Medienmaschine

### PR #248
`feat: connect live Agnes video to media factory` – MERGED.

Main/aktueller Snapshot-HEAD:
`99d3fecd204d4d0e577b9b2a9bb26ab9fb1f5da2`

`AgnesVideoAdapter`:
- ExecutionTruth = LIVE.
- verwendet bestehendes `AGNES_API_KEY` über GitHub Secrets.
- source-less VIDEO/REEL kann Agnes als Generator planen.
- erzeugtes MP4 wird über MediaStorageAdapter in R2 persistiert.
- Provenance: job/task/revision gebunden.
- MIME `video/mp4`, Größe und SHA-256 geprüft.

LIVE-Run:
GitHub Actions Run `36706431947`.

Verifiziert:
- Regression: SUCCESS.
- Blocks 1–6 Regression: SUCCESS.
- SOURCE-FACT-CONTRACT: SUCCESS.
- `live-video-r2`: SUCCESS.
- Agnes API Start: HTTP 200.
- Log-Nachweis:
  `AGNES VIDEO -> FACTORY ADAPTER -> R2 -> SHA-256: PASS`

Damit ist Agnes → Factory Adapter → R2 ein echter LIVE-Pfad.

Wichtig: Dieser Nachweis macht NICHT automatisch die gesamte Video-Editing-Kette LIVE. SupoClip/OpenChatCut bleiben bis zu ihren eigenen Live-Abnahmen SIMULATED.

## 6. Aktueller Wahrheitsstatus der Media-Maschinen

LIVE:
- Cloudflare R2 Media Storage.
- ImageRouter → R2.
- Agnes Video Generation → R2.
- FFmpeg lokaler Low-Level-Adapter, soweit bestehender Runtime-Pfad verwendet/getestet.

SIMULATED / noch zu ersetzen:
- SupoClip Contract-Adapter.
- OpenChatCut Contract-Adapter.
- ContractAV/Voice-Provider im CI-Kontext.
- CI-Publisher-Contract bleibt Simulation; bestehende reale Legacy-Publisher sind separat vorhanden.

Geplant/optional:
- Voice/TTS über vorhandene NVIDIA/Magpie-Richtung auf geeigneter Runtime.
- Avatar/Motion später.
- TikTok/YouTube Publishing erst bei echter Plattform-Inbetriebnahme.

## 7. Nächste Hauptmaschinen – SupoClip und OpenChatCut

Zielkette:
QUELLMATERIAL / GENERIERTES MATERIAL
→ SUPOCLIP
→ OPENCHATCUT
→ FFMPEG FINALISIERUNG
→ R2
→ FINAL QM / GOLDEN TABLET
→ HUMAN AUTHORITY
→ PUBLISHER.

### SupoClip
Zielrolle:
- Longform-/Quellvideo analysieren.
- interessante Segmente/Clips auswählen.
- Trim/Split/Merge/Short-Erzeugung.
- API-/Task-/Progress-/Export-Vertrag gegen echte Schnittstelle implementieren.
- erst nach realem Staffellauf ExecutionTruth auf LIVE.

### OpenChatCut
Zielrolle:
- eigentliche editierbare Timeline-/Editing-Maschine.
- Captions, Audio, Übergänge, Layer, targeted repair.
- Remotion/FFmpeg-basierter Export.
- MCP/HTTP-Adapter statt erfundener Cloud-API.
- zunächst Cloudflare Container als Test-Werkbank; später VPS möglich.
- Adaptergrenze so bauen, dass ein Wechsel Cloudflare Endpoint → VPS Endpoint die restliche Factory nicht verändert.

## 8. Cloudflare Container als Beta-Werkbank

Entscheidung 30.09.2026:
Für die aktuelle Lern-/Beta-Phase soll OpenChatCut zunächst in einem Cloudflare Container evaluiert werden, bevor ein VPS gekauft/fest dimensioniert wird.

Kein zweiter Cloudflare-Account nötig. Bestehender Account/R2 soll genutzt werden.

Architektur:
R2 Original/Source
→ Cloudflare Container lädt Arbeitsmaterial
→ OpenChatCut Timeline/Edit
→ Remotion/FFmpeg temporärer Render
→ fertiges MP4 zurück nach R2
→ temporäre Containerdaten dürfen verschwinden.

Grund:
- Containerdisk ist Werkbank/temporärer Workspace, nicht Archiv.
- reale CPU-/RAM-/Disk-/Renderzeit messen.
- Qualität, Quantität und Kosten pro fertigem Video ermitteln.
- VPS später anhand realer Messwerte dimensionieren statt raten.

Geplanter PoC/Benchmark:
1. 720×1280 / 7 s.
2. 1080×1920 / 15 s.
3. 1080×1920 / 30 s.
4. Caption-Layer.
5. Audio.
6. FFmpeg/Remotion Export.
7. Upload nach R2.
8. Download + SHA-256.
9. zusätzlich ffprobe/Decodierbarkeit, Dauer/Auflösung prüfen.
10. CPU/RAM/Disk/Wall-Time und Output-Größe protokollieren.

Erst nach bestandenem echten PoC darf der OpenChatCut-Adapter als LIVE bezeichnet werden.

## 9. Speicherstrategie – Lager vs. Werkbank

### R2 = dauerhaftes Lager
Dort gehören hin:
- wertvolle Originalmedien, soweit zulässig/gewollt.
- erzeugte Bilder.
- fertige Reels/Videos.
- Karussell-Assets.
- Audio/Voice.
- Untertitel.
- wichtige revisionsgebundene Zwischenstände.
- final freigegebene/veröffentlichte Medien.
- MediaRef/Provenance/Hash-bezogene Artefakte.

### Cloudflare Container = temporäre Werkbank
- Downloads aus R2.
- Render-Frames.
- temporäre Audio-/Video-Artefakte.
- OpenChatCut-/Remotion-/FFmpeg-Arbeitsdateien.
- nach erfolgreichem Export/R2-Persistierung löschbar.

### Späterer VPS
VPS-SSD wird Werkbank + Maschinenstandort:
- OpenChatCut.
- FFmpeg.
- Whisper/yt-dlp.
- Python-Agenten/Services.
- Cache/Logs/Arbeitsverzeichnisse.

R2 bleibt auch nach VPS-Migration das dauerhafte Medienlager. Dadurch ist kein großer Medienumzug nötig.

## 10. Spätere R2-Lifecycle-/Speicherstatistik

Noch NICHT als harte 30-Tage-Regel implementieren.

Zuerst echte Nutzung messen:
- Gesamtbelegung.
- Wachstum pro Woche/Monat.
- Speicher nach Typ: Original, final, Bild, Audio, Render-Zwischenstand.
- Alter.
- Job/Revision/Publish-Status.
- optional Kosten-/Operations-Statistik.

Danach Lifecycle-Policy datenbasiert festlegen, z. B. 30/60/90 Tage für eindeutig temporäre Artefakte.

Harte Schutzregel:
Final freigegebene/veröffentlichte Medien und bewusst archivierte Originale dürfen NICHT automatisch von einer Temp-Cleanup-Regel gelöscht werden.

## 11. Preview-Zugriff – noch offen

Bild und Agnes-MP4 liegen privat in R2. Der Bucket bleibt privat.

Noch zu bauen:
- sicherer Preview-/Download-Weg für Bülent.
- bevorzugt zeitlich begrenzter/protected Zugriff oder authentifizierter Factory-/Telegram-Preview.
- keine dauerhafte öffentliche R2-URL.
- tatsächliche Bild-/Video-Datei muss für Human Review sichtbar/abspielbar sein, bevor dieser UX-Punkt als fertig gilt.

## 12. Kosten-/Effizienzprinzip

Aktuelle Phase:
So günstig wie möglich echte Daten sammeln, aber nicht auf Kosten der technischen Wahrheit.

Bewertung für Media-Workloads:
- Qualität des Outputs.
- Quantität/Throughput.
- Renderzeit.
- CPU/RAM/Disk.
- Dateigröße/Storage.
- Kosten pro fertigem Asset.
- Zuverlässigkeit/Retry-Rate.

Cloudflare dient als Messstand. Wenn der Factory-Betrieb stabil ist, wird ein x86-VPS gegen dieselben Benchmarks getestet. Der VPS wird anhand realer Anforderungen ausgewählt.

## 13. Externe Accounts/Secrets – aktueller Grundsatz

Bereits vorhandene Infrastruktur nach Namen:
- Telegram.
- Meta/Instagram/Facebook Publisher.
- Groq.
- Gemini.
- OpenRouter.
- NVIDIA.
- Agnes.
- Apify.
- Cloudflare Workers AI.
- Cloudflare R2.

Secret-Werte bleiben ausschließlich in GitHub Actions Secrets bzw. sicherer Runtime-Konfiguration. Niemals Secret-Werte in Chat/Repo/Snapshot schreiben.

Neue kostenpflichtige Accounts nur dann anlegen, wenn vorhandene Werkzeuge die benötigte Aufgabe nicht wirtschaftlich/qualitativ erfüllen.

## 14. Offene technische Punkte – Priorität

P1:
1. OpenChatCut Cloudflare-Container PoC bauen und messen.
2. echten OpenChatCutAdapter implementieren.
3. realen Staffellauf OpenChatCut → FFmpeg/Export → R2 → SHA/ffprobe.
4. SupoClip echte Schnittstelle/Key/Auth verifizieren und LiveAdapter bauen.
5. End-to-End Quellvideo → SupoClip → OpenChatCut → FFmpeg → R2 testen.
6. sicheren Bild-/Video-Preview für Bülent bereitstellen.

P2:
7. prüfen, ob produktive Factory-Runtime R2 als tatsächliches Default-System-of-Record auswählt und nicht nur Live-Smokes.
8. boto3/Runtime-Dependency sauber in Produktionsinstallation verankern.
9. R2-Smoke-/Testobjekte gezielt aufräumen.
10. Retry-/Failure-/Crash-Verhalten für externe Media-Provider weiter red-teamen.
11. ffprobe/Codec-/Duration-/Resolution-Validierung für reale Videoartefakte standardisieren.

P3/später:
12. R2 Storage Analytics + Lifecycle.
13. Voice/TTS.
14. Avatar/Motion.
15. VPS-Benchmark/Migration.
16. TikTok/YouTube Publishing.

## 15. Offene Research-PRs

#231 `research: seed prompts.chat skill radar` ist weiterhin OPEN und nicht Teil des produktiven Main-Pfads.

Stale #242 bleibt CLOSED und darf den akzeptierten Block-6-Stand nicht überschreiben.

## 16. Wiederaufnahme in einem neuen Chat

Startanweisung:

"Lies zuerst `snapshots/SNAPSHOT_2026-09-30_CONTENT_FACTORY_LIVE_MEDIA_CLOUD_WORKBENCH.md`, danach `PROJECT_GUARDRAILS.md`. Prüfe den aktuellen Main gegen Snapshot-HEAD `99d3fecd204d4d0e577b9b2a9bb26ab9fb1f5da2`. Setze bei P1 fort: OpenChatCut Cloudflare-Container PoC → echter Adapter → Live-Staffellauf → SupoClip Live-Integration → vollständige Video-Kette. R2 bleibt privates dauerhaftes Medienlager. SIMULATED niemals als LIVE ausgeben. Human Authority bleibt Bülent."

## 17. Leitsatz

GitHub = Baupläne und Software.  
Cloudflare Container / später VPS = Werkbank und Maschinen.  
R2 = dauerhaftes Medienlager.  
Factory Contracts = Förderband.  
Golden Tablet = Human Preview.  
Bülent = finale Veröffentlichungsautorität.

Ziel ist nicht nur "es läuft", sondern messbare Qualität + Quantität + Effizienz bei nachvollziehbarer Provenance und sicherer Human Authority.
