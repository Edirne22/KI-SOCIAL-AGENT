# ADR – Content Factory Tool Battle

Datum: 2026-09-29
Status: PROPOSED – vor Implementierung
Scope: Media-/Video-Content-Fabrik

## Entscheidung in Kurzform

Kein monolithisches All-in-One-Tool wird zum alleinigen Fundament.

MVP-Stack:
1. KI-SOCIAL-AGENT Python Betriebsleiter/Orchestrator bleibt System of Record.
2. OpenChatCut wird primärer Kandidat für editierbare Timeline, Agent-/MCP-Zugriff, Captions, Projektpersistenz und Render-Arbeitsfläche.
3. FFmpeg bleibt robuste technische Basis/Fallback für Medienoperationen.
4. Der bestehende Publisher und die bestehende Human-Approval-Kette bleiben zunächst produktiv.
5. OpenCut-AI dient als Feature-Referenz bzw. möglicher Spender für lokale AI-Media-Funktionen.
6. Postiz wird später als Multi-Plattform-Publishing-Gateway evaluiert.
7. Voice und Avatar werden als austauschbare Adapter gebaut und blockieren MVP 1 nicht.

## Produktionshalle

### OpenChatCut – primärer Kandidat
Stärken:
- local-first
- echte editierbare Multitrack-Timeline
- externe Agenten über MCP
- Agent Skills
- Änderungen über gemeinsame EditorCore-Kommandos
- proposal-/undo-fähige Bearbeitung
- Wort-Level-Transkript und textbasierte Schnitte
- gekoppelte Captions
- Bilder, Video, Sprache, Musik und SFX als Medien-/Generierungsbausteine
- Motion Graphics, Effekte, Übergänge
- MP4, Audio, Captions, FCPXML und vollständige Projektdaten als Export
- Windows-Desktop/Source-Workflow
- NVENC auf kompatiblen Windows-Systemen
- lokale Projekt-/Mediendaten
- AGPL-3.0-or-later

Besonders wichtig für unsere Architektur:
Ein Agent kann ein vorhandenes Projekt lesen und gezielt ändern. Dadurch kann Feedback wie "bei Sekunde 23 anderes Bild" als Targeted Repair umgesetzt werden, statt das komplette Reel neu zu generieren.

Risiken:
- aktives/junges Projekt; Schnittstellen können sich verändern
- Node 24 / TypeScript/Electron neben unserer Python-Welt
- Remotion ist Bestandteil des Render-Stacks und besitzt eigene Lizenzbedingungen
- Cloud-/Generierungsfunktionen hängen teilweise von konfigurierten Drittanbietern ab

Entscheidung:
Primärer Integrationskandidat, aber hinter einem eigenen Adapter kapseln.

### OpenCut-AI – Feature-Referenz / sekundärer Kandidat
Stärken:
- MIT-Projekt
- lokales FFmpeg
- Whisper-Transkription mit Wort-Timestamps
- textbasiertes Editing
- lokale AI-Dubbing-Pipeline
- Auto-B-Roll aus eigener Mediathek via CLIP
- Background Removal
- Untertitel
- Voice/TTS-Funktionen
- AI-Studio/Fact-Check-Funktionen

Risiken:
- deutlich kleineres Maintainer-/Projektprofil
- einzelne eingebundene Modelle besitzen restriktivere Lizenzen als der MIT-Anwendungscode
- XTTS-v2 insbesondere nicht als langfristige kommerzielle Voice-Basis fest einplanen

Entscheidung:
Nicht verwerfen. Funktionen und Implementierungsideen gezielt gegen OpenChatCut vergleichen; nützliche Fähigkeiten über eigene Adapter ergänzen.

### FFmpeg
Rolle:
- stabiler Low-Level-Media-Layer
- Probe, Transcode, Audio-Extraktion, Concatenate, Overlay, Formatierung
- Fallback, damit die Fabrik nicht von einem UI-/Editor-Projekt abhängig wird

Entscheidung:
Pflichtbestandteil der Basis.

### Remotion
Stärken:
- programmatische Video-Komposition
- sehr gut für Templates, Motion Graphics und reproduzierbare React-basierte Videos
- bereits in OpenChatCut integriert

Risiko:
Lizenzbedingungen unterscheiden zwischen kleinen Creator-Nutzungen und bestimmten automatisierten Video-Produkten/Organisationen.

Entscheidung:
Über OpenChatCut nutzbar und technisch wertvoll, aber nicht als unersetzbares proprietäres Kernformat unserer Job-Definition verwenden. Lizenz vor produktiver Skalierung erneut prüfen.

## Betriebsleiter / Orchestrierung

Der bestehende Python-Stack bleibt die übergeordnete Steuerung.

Der Betriebsleiter verwaltet:
- Production Job ID
- Statusmaschine
- Quellen und Timestamps
- Transkript
- Claims/Faktenbelege
- Writing
- Storyboard
- Assets
- Voice
- Captions
- Render
- QM
- Human Approval
- Publish-Handoff

OpenChatCut ist Werkzeug des Betriebsleiters, nicht dessen Ersatz.

Pipecat:
Technisch stark für Echtzeit-Voice-/Multimodal-Agenten und Multi-Agent-Handoffs. Für den ersten asynchronen Reel-Produktions-MVP jedoch zusätzliche Komplexität ohne zwingenden Nutzen.

Entscheidung:
WATCH / spätere Voice- oder Echtzeitstufe; nicht MVP-Orchestrator.

## Transkription

MVP:
- bestehende/lokale Whisper-/faster-whisper-Strategie bevorzugen
- Wort-Timestamps persistieren
- Quell-Timestamps durch alle nachfolgenden Stufen erhalten

OpenWhispr:
Interessant als lokales, plattformübergreifendes Speech-to-Text-/Agentenwerkzeug, aber stärker auf Dictation/Meetings ausgerichtet als auf unsere Headless-Media-Pipeline.

Entscheidung:
WATCH; Kerntranskription zunächst direkt als Adapter.

## Voice

### Übergangsstimme
Für MVP genügt eine klar lizenzierte künstliche Stimme.

Kokoro:
- sehr leichtgewichtig
- permissive Modell-/Codevarianten vorhanden
- gute Option für Übergangsstimme
- kein echtes Voice-Cloning im Kern

Entscheidung:
Kandidat für Phase 1.

### Voice-Cloning
XTTS v2 und F5-TTS sind technisch attraktiv, aber die verfügbaren vortrainierten Modelle besitzen Lizenzbeschränkungen, die für eine langfristig möglicherweise kommerzielle Social-Media-Fabrik problematisch sind.

Entscheidung:
Nicht als dauerhaftes Fundament fest verdrahten.
VoiceAdapter definieren und später ein Modell/API mit passender Lizenz und guter DE/TR-Qualität auswählen.
Eigene Stimme nur mit Bülents ausdrücklicher Zustimmung/Material verwenden.

## Avatar / Lip-Sync

MVP 1:
kein Avatar-Zwang. Erst funktionierender End-to-End-Reel-Job.

Spätere Kandidaten:
- MuseTalk für Lip-Sync: Projektcode und trainiertes Modell laut Projekt auch kommerziell nutzbar; Abhängigkeiten separat prüfen.
- LivePortrait für Animation interessant; bei kommerzieller Nutzung muss insbesondere die InsightFace-Modellabhängigkeit ersetzt/korrekt lizenziert werden.

Entscheidung:
AvatarAdapter vorsehen, Implementierung nach Rendering-MVP.

## Publisher Battle

### Bestehender KI-SOCIAL-AGENT Publisher
Stärken:
- bereits live bewiesen
- Human Approval funktioniert
- Queue/Claim/Cadence bereits gehärtet
- Instagram/Facebook produktiv bekannt

Entscheidung:
MVP-Sieger. Nicht ersetzen.

### Postiz
Stärken:
- self-hosted
- AGPL-3.0
- Public API und Webhooks
- MCP/CLI/Agent-Integration
- Multi-Plattform
- Scheduling/Cross-Posting
- offizielle OAuth-Flows
- self-hosted ohne Postiz-Cloud-Abo; eigene Infrastruktur
- geeignet als zukünftiges Gateway für Instagram/Facebook/TikTok/X/YouTube und weitere Plattformen

Nachteile:
- zusätzliche Postgres/Redis/Service-Komplexität
- eigene Developer-Apps/Plattformfreigaben nötig; Meta/YouTube/TikTok können Vorlauf benötigen
- bestehende funktionierende Publisherlogik würde unnötig gefährdet, wenn sofort ersetzt

Entscheidung:
Phase 2/3 als PublisherAdapter/PostizGateway integrieren. Human Approval bleibt vor dem Gateway.

### Mixpost
Stärken:
- Self-hosting
- Lite-Version MIT
- solides Social-Media-Management

Nachteile:
- Lite/Pro-Trennung
- für unsere agentische API/MCP-Strategie weniger attraktiv als Postiz

Entscheidung:
Fallback/Alternative, derzeit nicht erste Integrationswahl.

## Zielarchitektur

Bülent/Telegram/API
→ Python Betriebsleiter
→ Production Job Store
→ Source/Ingest Adapter
→ Transcription Adapter
→ Highlight/Fact/Writing Agents
→ Storyboard
→ VideoEditorAdapter
   → OpenChatCut primär
   → FFmpeg fallback
   → OpenCut-AI-Funktionen optional
→ VoiceAdapter
→ AvatarAdapter optional
→ Caption/Render
→ End-QM
→ Repo/Telegram Preview
→ Bülent Human Approval
→ PublisherAdapter
   → bestehender Publisher zuerst
   → Postiz später
→ Instagram/Facebook/TikTok/YouTube/X

## MVP-Reihenfolge

1. Production-Job-Schema + Statusmaschine.
2. VideoEditorAdapter definieren.
3. OpenChatCut Proof of Concept: Projekt anlegen, Assets importieren, Timeline ändern, Caption setzen, vertikales MP4 exportieren.
4. FFmpeg-Fallback-Test.
5. lokales Transkript + Wort-Timestamps.
6. Highlights/Claims/Fakten/Writing.
7. Storyboard → Timeline.
8. Übergangsstimme.
9. Captions + 9:16 Render.
10. Repo/Telegram Preview.
11. bestehende Human Approval.
12. bestehender Publisher.
13. Targeted Repair E2E.
14. danach Voice-Cloning.
15. danach Avatar/Lip-Sync.
16. danach Postiz + TikTok/YouTube/X.
17. Hardening/Regression/Red-Team/Live-E2E.

## Abnahmekriterium für MVP 1

Ein Auftrag mit lokalem oder autorisiertem Quellmaterial erzeugt reproduzierbar:
- persistentes Transkript mit Timestamps
- drei bis fünf ausgewählte/prüfbare Punkte
- eigenes Skript
- Storyboard
- editierbares Videoprojekt
- Voice
- synchrone Captions
- vertikales MP4
- QM-Bericht
- Vorschau zur menschlichen Freigabe

Eine Korrektur wie "Sekunde 23: anderes Bild" verändert nur den betroffenen Teil und erzeugt eine neue Version. Veröffentlichung erfolgt ausschließlich nach expliziter Human Approval.

## Architekturregel

Kein externes Tool darf System of Record für unsere Fakten, Freigaben oder Production Jobs werden. Alle externen Tools werden über Adapter gekapselt und müssen austauschbar bleiben.


## Vierte Architekturentscheidung: Factory Frontend + Job API + Media Storage

Die fertige Fabrik darf nicht davon abhängen, dass Bülent einen ChatGPT-Chat öffnet. ChatGPT bleibt Entwicklungs-/Programmierpartner; die produktive Fabrik erhält eine eigene Bedienoberfläche.

### Factory Frontend

Ziel ist eine bewusst einfache Weboberfläche:
- großes Auftragseingabefeld
- Plus-Button für Bilder, Videos, Audio und Dokumente
- Mikrofon-Button für freie Spracheingabe
- sichtbares/korrigierbares Transkript vor Job-Übergabe
- Senden/Produktion starten
- Liste laufender Production Jobs und deren Status
- Video-/Asset-Vorschau
- Human-Approval-Aktionen: Ändern / Verwerfen / Posten
- später Timeline-/Timestamp-Feedback, z. B. "00:23 anderes Bild"

Die Oberfläche ist nur ein Client. Sie enthält keine eigene Fabriklogik.

### Mehrere Eingänge, ein Betriebsleiter

Alle Eingänge werden auf dasselbe Job-Protokoll normalisiert:

Web-App
Telegram
spätere Clients
→ Job API
→ Python Betriebsleiter
→ dieselbe Content-Fabrik.

Telegram bleibt für mobile Kurzbefehle, Status, Preview und schnelle Freigaben erhalten. Die Web-App ist der primäre Arbeitsplatz für Upload, Spracheingabe, Projektansicht und detaillierte Korrekturen.

### Spracheingabe

Der Mikrofon-Button erzeugt zunächst eine Audioaufnahme.
SpeechToTextAdapter:
- transkribiert lokal oder über einen austauschbaren Provider
- bevorzugt Whisper/faster-whisper für lokalen Betrieb
- speichert Originalaudio + Transkript
- zeigt das Transkript vor dem Start zur Korrektur
- übergibt dem Betriebsleiter einen strukturierten Textauftrag

Das Originalaudio bleibt als Job-Artefakt erhalten; der Text ist die maschinenlesbare Arbeitsanweisung.

### Job API

Die Job API ist die stabile Grenze zwischen Benutzeroberflächen und Fabrik.

MVP-Endpunkte/Funktionen:
- Production Job erstellen
- Dateien registrieren/hochladen
- Spracheingabe/Transkript anhängen
- Jobstatus lesen
- Preview/Artefakte abrufen
- Änderungsauftrag mit optionalem Timestamp senden
- Human Approval setzen
- Publish-Handoff auslösen

Frontend und Telegram dürfen keine internen Agenten direkt aufrufen.

### Media Storage

Große Binärdateien werden nicht regulär in Git versioniert.

In Media Storage gehören:
- Rohvideos
- Bilder
- Audio
- extrahierte Frames
- Proxy-Dateien
- Voice-Ausgaben
- Zwischenrenders
- finale Videos

Im Production Job werden stattdessen Media-ID/URI, Hash, Dateityp, Größe, Herkunft, Erstellungszeit und Version gespeichert.

MediaStorageAdapter kapselt den Speicherort. Unterstützbare Backends:
1. lokaler Arbeitsordner auf Windows für Entwicklung
2. persistenter VPS-Speicher für Serverbetrieb
3. NAS/SMB als optionaler Speicher
4. S3-kompatibler Object Storage als spätere robuste Variante
5. Router-USB-Speicher optional als Archiv/Backup/Übergabespeicher

### Router-USB / externe Festplatte

Eine 32/64-GB-USB-Platte am Heimrouter ist technisch als Netzwerkspeicher möglich, sofern der Router SMB/NAS-Freigaben zuverlässig bereitstellt. Sie ist jedoch nicht als primärer Production Storage vorgesehen.

Gründe:
- Router-USB/CPU kann bei großen Video-I/O-Operationen langsam sein
- Heimnetz-/Internet-Ausfall würde entfernte Worker blockieren
- SMB über das öffentliche Internet soll nicht direkt exponiert werden
- konkurrierende Render-/Transkriptionsjobs benötigen robustere I/O-Eigenschaften
- 32/64 GB sind für Rohvideo und Zwischenrenders schnell erschöpft

Empfehlung:
- Router-USB: Archiv, Backup oder manuelle Übergabe
- externe SSD/HDD an dauerhaft laufendem PC/NAS: besser für lokalen großen Medienspeicher
- VPS/Object Storage: besser für autonome 24/7-Serverjobs

Falls Heim-NAS später vom VPS benötigt wird, Zugriff nur über einen sicheren privaten Tunnel/VPN und nicht durch öffentlich freigegebenes SMB.

### Storage-Regel

Agentencode, Konfiguration und kleine textuelle Job-Artefakte bleiben in Git/GitHub.
Schwere Medien liegen im Media Storage.
Die Fabrik referenziert Medien über MediaStorageAdapter und darf keinen festen lokalen Pfad als Architekturannahme einbauen.

### Erweiterte Zielarchitektur

Factory Web UI ─┐
Telegram ───────┼→ Job API → Python Betriebsleiter → Production Job Store
weitere Clients ┘                         │
                                         ├→ MediaStorageAdapter
                                         ├→ Transcription/Fact/Writing
                                         ├→ VideoEditorAdapter
                                         ├→ Voice/Avatar/Caption/Render
                                         └→ End-QM
                                                ↓
                                      Repo/Web/Telegram Preview
                                                ↓
                                         Bülent Approval
                                                ↓
                                         PublisherAdapter

### Auswirkung auf MVP-Reihenfolge

Vor dem eigentlichen Video-PoC werden die stabilen Grenzen definiert:
1. Production-Job-Schema + Statusmaschine.
2. MediaStorageAdapter + lokales Development-Backend.
3. Job-API-Vertrag.
4. minimales Factory-Frontend für Textauftrag, Upload und Status.
5. Spracheingabe/STT kann direkt danach ergänzt werden.
6. VideoEditorAdapter/OpenChatCut-PoC.
7. restliche Produktionskette wie oben.

Damit kann die Fabrik später vom Windows-PC auf VPS/NAS/Object Storage umziehen, ohne Frontend, Agentenlogik oder Production Jobs neu zu entwerfen.


## Media-Storage-Entscheidung: Cloudflare R2 zuerst

Für den ersten produktiven MediaStorageAdapter wird Cloudflare R2 als bevorzugtes Remote-Backend vorgesehen.

Gründe:
- S3-kompatible API
- für unseren geplanten Start ausreichend attraktiver Free-Tier
- niedrige Speicherkosten bei Wachstum
- keine Architekturbindung, da Zugriff ausschließlich über MediaStorageAdapter erfolgt
- geeignet für Originalmedien, relevante Job-Artefakte und finale Render-Ausgaben

Betriebsmodell:
- Windows-PC/VPS = aktive Werkbank für Download, Transkription, Proxies und Rendering
- Cloudflare R2 = persistentes Medienlager
- Git/GitHub = Code, Job-Metadaten, Skripte, Quellen-/QM-Dokumentation und kleine textuelle Artefakte
- Router-USB/externe Platte = optionales zusätzliches Archiv/Backup

Temporäre Frames, Proxies und Zwischenrenders sollen nach erfolgreichem Jobabschluss gemäß Retention-Regel automatisch bereinigt werden, damit Remote-Speicher nicht unnötig wächst.

Fallbacks:
Backblaze B2, andere S3-kompatible Anbieter, NAS oder lokaler/VPS-Speicher bleiben durch den Adapter austauschbar. R2 ist die Startentscheidung, kein Vendor-Lock-in.


## Tool-Battle Nachtrag: SupoClip als Reel Automation Engine

Fund vom 29.09.2026: FujiwaraChoki/supoclip wurde nach Repo/Dokumentation gegen OpenChatCut, FFmpeg und die geplante Edirne-22-Architektur geprüft.

### SupoClip – Stärken

SupoClip bildet bereits einen großen Teil einer automatischen Short-Video-Pipeline ab:
- Longform-Video bzw. Upload/YouTube als Eingang
- Transkription mit Wort-Timestamps
- LLM-basierte Auswahl mehrerer clip-würdiger Segmente
- Virality-/Hook-Bewertung
- automatisches vertikales 9:16 Face-Cropping
- wortgenaue animierte Untertitel
- Hook-Titel
- optional B-Roll/Transitions
- integrierter Trim/Split/Merge-Editor
- Reels/TikTok/Shorts-Export
- asynchrone Verarbeitung und Live-Fortschritt
- REST API
- separater MCP-Server

Self-host Architektur:
Frontend (Next.js)
→ FastAPI
→ Redis Queue
→ ARQ Worker
→ FFmpeg/Video-Pipeline
↔ PostgreSQL
→ SSE Progress.

Das passt sehr gut zum geplanten VPS-Betrieb und zu einem Betriebsleiter, der Jobs über eine API an eine spezialisierte Video-Maschine delegiert.

### SupoClip – Grenzen/Risiken

- Standard-Transkription benötigt derzeit AssemblyAI; Edirne 22 soll dies hinter TranscriptionAdapter kapseln und lokale/freie Alternativen ermöglichen.
- SupoClip ist AGPL-3.0. Keine blinde Code-Übernahme in unseren Kern. Bevorzugt als klar abgegrenzter, separat deploybarer Dienst hinter Adapter/API betreiben und Lizenzpflichten einhalten.
- Projekt ist jung; Dokumentation zum Testbestand ist nicht vollständig konsistent. Unsere eigenen Regression-, Recovery-, QM- und Red-Team-Gates bleiben verbindlich.
- Clip-Auswahl/Virality-Scoring darf nicht System of Record für Racing-Fakten oder Bülent-Writing werden. Diese Verantwortung bleibt bei unseren bestehenden Agenten.
- Die automatische Clip-Pipeline ersetzt noch nicht die fein steuerbare Targeted-Repair-Timeline.

### Vergleich der drei Video-Maschinen

#### SupoClip
Rolle: automatische Reel/Shorts-Erzeugung aus längerem Quellmaterial.

Ideal für:
- Longform → 3–7 Short-Kandidaten
- automatische Segmentwahl
- Face Crop
- schnelle 9:16-Produktion
- Captions/Hook/B-Roll
- serverseitige Queue-Verarbeitung

#### OpenChatCut
Rolle: agentisch steuerbarer, editierbarer Timeline-/Repair-Motor.

Ideal für:
- echte Timeline
- präzise Änderungen
- Agent/MCP-Kommandos auf dasselbe Projekt
- Undo/traceable Commands
- Effekte/Transitions/Multitrack
- Targeted Repair wie "00:23 anderes Bild"
- editierbares Masterprojekt
- R2-fähige Media-Persistence

#### FFmpeg
Rolle: stabile unterste Medien-/Render-Schicht und Fallback.

Ideal für:
- Transcode
- Audio/Video Extraktion
- Concatenate/Crop/Scale
- einfache Caption-/Overlay-Operationen
- reproduzierbare Headless-Exports
- Recovery/Fallback, wenn höherer Editor ausfällt

### Neue Maschinenverteilung

Die Tools werden nicht gegeneinander als Monolith ausgewählt. Sie bekommen getrennte Verantwortungen:

Betriebsleiter
→ Source/Transcription/Fact/Writing/Storyboard
→ ReelEngineAdapter
   → SupoClip primär für automatische Longform→Short-Produktion
→ VideoEditorAdapter
   → OpenChatCut für editierbares Masterprojekt und gezielte Reparaturen
→ RenderAdapter
   → FFmpeg als technische Basis/Fallback
→ R2
→ End-QM
→ Bülent Approval
→ Publisher.

Wichtig: Für MVP muss nicht jeder Job zwingend durch beide Editoren laufen. Ein einfacher automatisch erzeugter Short darf SupoClip → QM → Preview nehmen. OpenChatCut wird dann eingesetzt, wenn ein editierbares Masterprojekt, aufwendigere Gestaltung oder Targeted Repair benötigt wird.

### Was wir aus SupoClip übernehmen – und was nicht

Übernehmen/integrieren:
- Job-/Worker-Prinzip
- REST/MCP-Ansteuerung
- automatische Short-Kandidaten
- Face Crop
- Caption-/Hook-Pipeline
- B-Roll-Konzept
- Fortschrittsmodell als Referenz
- serverseitige Docker-Deployment-Idee

Nicht an SupoClip abgeben:
- Racing Discovery
- Quellenvertrag
- Fact Check
- Series Lock
- Bülent Voice/Writing
- Human Authority
- endgültiger Approval State
- Publisher-Entscheidung
- ProductionJob als kanonisches System of Record

### PoC-Gate vor tiefer Integration

Vor produktiver Bindung wird ein isolierter SupoClip-PoC auf dem künftigen VPS durchgeführt:
1. Docker-Stack starten.
2. autorisiertes/lokales Testvideo einspeisen.
3. REST API/MCP Job starten.
4. Segmentauswahl prüfen.
5. 9:16 Face Crop prüfen.
6. DE/TR Captions und Sonderzeichen prüfen.
7. Renderzeit, CPU/RAM und Scratch-Speicher messen.
8. Job-Abbruch/Resume/Fehlerfall testen.
9. Ausgabe in Cloudflare R2 übernehmen.
10. Ergebnis durch Edirne-22 End-QM laufen lassen.
11. prüfen, ob SupoClip-Ausgabe ohne OpenChatCut publikationsfähig ist.
12. Targeted-Repair-Fall gegen OpenChatCut testen.

Erst anhand dieses PoC entscheiden wir, wie häufig OpenChatCut im Normalpfad benötigt wird.

### Aktualisierte MVP-Priorität

1. ProductionJob + Statusmaschine.
2. MediaStorageAdapter: Local/Scratch + Cloudflare R2.
3. Job API/Betriebsleiter-Grenze.
4. SupoClipAdapter + isolierter VPS-PoC.
5. TranscriptionAdapter entkoppeln.
6. bestehende Fact/Writing/Storyboard-Kette anbinden.
7. SupoClip → R2 → End-QM → Preview E2E.
8. OpenChatCutAdapter für editierbares Projekt/Targeted Repair.
9. Human Approval + bestehender Publisher.
10. Voice/Avatar danach.

Damit wird nicht zuerst ein eigener Videoeditor nachgebaut. Wir nutzen vorhandene spezialisierte Maschinen und konzentrieren eigene Entwicklung auf Orchestrierung, Faktenqualität, Bülent-Stil, Human Authority und den durchgängigen Produktionsworkflow.


## Radar-Nachtrag: Discovery, Trend Intelligence und Generative Video

Funde vom 29.09.2026 aus Bülents laufendem Tool-Radar. Diese Kandidaten erweitern den Beobachtungsraum, ändern aber bewusst **nicht** die aktuelle MVP-Priorität mit ProductionJob, R2, Job API, SupoClip und anschließend OpenChatCut.

### Futurepedia – Discovery-Radar

Rolle:
- Verzeichnis/Entdeckungsquelle für neue KI-Tools, Modelle und Workflows.
- Kann regelmäßig genutzt werden, um neue Kandidaten für Video, Audio, Automation, Coding und Agenten zu entdecken.

Architekturentscheidung:
- **RADAR / WATCH.**
- Kein Runtime-Baustein und kein System of Record.
- Interessante Funde werden einzeln gegen Lizenz, Self-Hosting, API/MCP, Kosten, Reifegrad und Nutzen für Edirne 22 geprüft.
- Ziel ist nicht, möglichst viele Tools einzubauen, sondern früh bessere austauschbare Maschinen zu entdecken.

### ViralityAI – Trend-/Content-Intelligence

Potenzielle Rolle:
- Recherche nach erfolgreichen Content-Ideen und Mustern auf Social-Plattformen.
- Analyse von Hook, Lesbarkeit, Retention/Pacing, Shareability, CTA sowie Format-/Content-Signalen kann als zusätzliche Input-Schicht für Themenwahl und Storyboard dienen.

Möglicher späterer Pfad:
Racing Discovery
→ Trend-/Virality-Signale
→ Betriebsleiter
→ Fact Check / Quellenvertrag
→ Bülent Writing
→ Reel Engine
→ End-QM.

Harte Grenze:
- Virality-/Performance-Signale sind **keine Faktenquelle**.
- Ein hoher Viralitätswert darf niemals Source-Fact-Contract, Series Lock, Fact Check oder Human Authority überstimmen.
- Externe Scores werden höchstens als beratendes Signal im ProductionJob gespeichert.

Architekturentscheidung:
- **WATCH / LATER.**
- Erst evaluieren, wenn der eigentliche Produktionspfad stabil ist.
- Wenn integriert, ausschließlich hinter einem eigenen ContentIntelligenceAdapter.

### Luma Agents / Luma AI – Generative Video und spätere Avatar-Stufe

Potenzielle Rolle:
- Generative Bilder/Video und agentisch erzeugte oder veränderte Szenen.
- Interessant für spätere Edirne-22-Avatar-/Character-Animation, visuelle Inserts, Bewegungen, Lip-Sync-/Character-Szenen und generative Ergänzungen.
- API-basierte Job-Ansteuerung passt grundsätzlich zum Adapter-/Betriebsleiter-Modell.

Möglicher späterer Pfad:
Betriebsleiter
→ AvatarEngineAdapter / GenerativeVideoAdapter
→ Luma oder alternativer Provider
→ MediaStorage/R2
→ VideoEditor/Reel Engine
→ End-QM.

Architekturentscheidung:
- **LATER / WATCH**, nicht MVP 1.
- Luma wird nicht System of Record und nicht fest in ProductionJob verdrahtet.
- Kosten, API-Bedingungen, Nutzungs-/Outputrechte, DE/TR-Qualität, Character Consistency und Reproduzierbarkeit müssen vor produktiver Bindung separat geprüft werden.
- Der Adapter muss einen späteren Wechsel zu einem anderen lokalen oder gehosteten Modell erlauben.

### Nicht als Runtime-Bausteine priorisiert

Nick Saraev / Liam Ottley:
- mögliche Lern-/Architektur-/Workflow-Quellen für Agenten und Automatisierung.
- **RADAR**, keine Runtime-Abhängigkeit.

Cursor:
- Entwicklungswerkzeug/IDE-Assistent.
- derzeit kein Bestandteil der produktiven Content Factory und kein Ersatz für Betriebsleiter, GitHub-Workflow oder Runtime-Agenten.

### Radar-Regel

Bülent kann während des Aufbaus jederzeit neue Tools, Repositories, Videos, Screenshots oder Dienste einwerfen. Jeder Fund wird nach demselben Raster bewertet:
1. Welche konkrete Maschinenrolle könnte er übernehmen?
2. Spart er eigene Entwicklungsarbeit?
3. Self-hosted/Open Source/API/MCP?
4. Lizenz und mögliche kommerzielle Nutzung?
5. Kosten und Infrastrukturbedarf?
6. Reifegrad, Tests, Recovery und Wartbarkeit?
7. Kann er hinter einen Edirne-22-Adapter?
8. Ersetzt er eine bestehende Maschine oder ergänzt er nur?
9. Gefährdet er Fakten-QM, Human Authority oder das kanonische ProductionJob-Modell?
10. MVP, WATCH/LATER oder verwerfen?

Leitprinzip bleibt:
**Wir setzen unsere Fabrik über die besten verfügbaren Maschinen, statt jede Maschine unnötig selbst nachzubauen.**


## Pollo MCP/CLI – GenerativeMediaAdapter-Kandidat

**Entscheidung:** Pollo wird als konkreter PoC-Kandidat für die generative Medienmaschine aufgenommen; SupoClip bleibt der priorisierte Longform→Short/Reel-Kandidat.

Maschinenaufteilung:
- SupoClip: bestehendes Video → Segmentwahl, Hook, 9:16, Captions, Short/Reel.
- Pollo MCP/CLI: neue Bilder/Videos/B-Roll bzw. fehlende generative Szenen hinter `GenerativeMediaAdapter`.
- OpenChatCut: editierbarer Master/Targeted Repair.
- FFmpeg: Low-Level/Fallback.

Architekturgrenze:
`Betriebsleiter → GenerativeMediaAdapter → Pollo → MediaStorageAdapter/R2 → nächste Maschine`.

Keine Pollo-eigene Job-, Fakten-, Approval- oder Publisher-Hoheit. Ergebnisassets müssen vor Weitergabe in den kanonischen ProductionJob übernommen und mit Media-ID/URI/SHA-256/MIME/Größe/Provenienz/Revision gebunden werden.

### Pollo-PoC-Gate
1. MCP/CLI-Verbindung isoliert herstellen.
2. Auftrag aus einem ProductionJob ableiten.
3. Referenzasset über sicheren Storage-Handoff übergeben.
4. Generierungsjob starten und Task-/Statuskorrelation prüfen.
5. Timeout, Providerfehler und Retry ohne Doppeljob testen.
6. Ergebnis in MediaStorage/R2 übernehmen statt Provider-URL zum dauerhaften System of Record zu machen.
7. Hash, MIME, Größe, Provenienz und Revision prüfen.
8. Ergebnis an nachfolgende Maschinenrolle übergeben.
9. veraltete Revision und fremde Job-ID im Handoff blockieren.
10. DE/TR, Kosten, Rechte/Lizenzbedingungen und Datenfluss prüfen.
11. Staffellauf vom ersten Bülent-Befehl bis zum aktuell implementierten Endpunkt wiederholen.
12. Pollo gegen alternative GenerativeMediaAdapter-Provider austauschbar halten.

**Wichtig:** Eine Marketingaussage zu kostenlos/unbegrenzt oder zu einzelnen verfügbaren Modellen wird nicht als dauerhafte Architekturannahme behandelt. Preise, Limits, Modelle und Rechte werden beim PoC frisch verifiziert.
