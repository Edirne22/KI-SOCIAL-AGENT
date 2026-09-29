# IDEEN-POOL – externe Open-Source-Bausteine

Stand: 2026-09-29

## P1 – aktive Untersuchung

### Pipecat (pipecat-ai/pipecat)
Ziel: Prüfen als Basis für die geplante Audio-/Sprachstufe.
Relevante Bausteine:
- frame-basierte Audio/Text/Video-Pipelines
- STT/TTS und Voice-Agent-Integration
- WebSocket/WebRTC-Transports
- parallele Pipelines / Multi-Agent-Handoffs
- mögliche Kette: Telegram/Video/Audio -> STT -> bestehender Research/Racing-Stack -> bestehende Fakten-/Writing-/Chief-QM
Grundsatz: Pipecat ersetzt NICHT die Racing-QM. Truth/QM bleibt unverändert hinter der Transkription.
Lizenz vor jeder Codeübernahme erneut prüfen und Hinweise erhalten.

### Postiz (gitroomhq/postiz-app)
Ziel: Prüfen, ob Postiz unser Social-Publishing-Backend für Instagram/Facebook/TikTok werden kann.
Relevante Bausteine:
- Public API / Webhooks
- Scheduling und Kalender
- Plattform-Provider/OAuth
- Retries, Token-Refresh, durable Workflows
- Analytics
Zielarchitektur: Edirne-22 Content/QM -> Telegram-Freigabe -> dünner Postiz-Adapter -> Social-Plattformen.
WICHTIG: AGPL-3.0. Keine direkte Codekopie in KI-SOCIAL-AGENT ohne separate Lizenz-/Architekturentscheidung. Bevorzugt getrennte Self-Hosted-Instanz + API-Adapter.

## P2 – im Blick behalten

### AnythingLLM (Mintplex-Labs/anything-llm)
Prüfkandidat für Memory/RAG, Dokument-Ingestion und Retrieval. Interessant für Rider/Event/Source/Community-Memory und natürliche Archivabfragen.

### CrewAI (crewAIInc/crewAI)
Prüfkandidat für Orchestrierungs-Patterns: Agentenrollen, Handoffs, Parallelisierung, Retry/State/Observability. Keine Migration des funktionierenden Racing-Stacks ohne nachgewiesenen Mehrwert.

### Cline (cline/cline)
Prüfkandidat als Entwicklungswerkzeug/CLI/IDE-Agent für Laptop/VPS und Repo-Arbeit; nicht als Kern des Racing-Runtimes.

## Verbindliche Integrationsregeln
- PROJECT_GUARDRAILS.md bleibt bindend.
- Racing-/Source-Fact-/Semantic-/Writing-/Chief-QM werden durch externe Frameworks nicht umgangen oder abgeschwächt.
- Erst Architektur/License/Failure-Modes analysieren, dann kleiner Adapter/Spike auf Branch.
- Keine Fremdframework-Migration nur wegen Feature-Overlap.
- Jede produktive Integration durchläuft: BUILD -> REGRESSION -> CI -> RED-TEAM -> POSITIVE CONTROL -> ROOT-CAUSE/FIX -> ATTACK AGAIN -> CI GREEN -> Merge-Freigabe.
