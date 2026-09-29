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
