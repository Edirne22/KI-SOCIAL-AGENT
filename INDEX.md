# EDIRNE 22 — Projektzentrale / anklickbarer Index

**Start hier.** [Aktuelle Architektur](docs/ARCHITEKTUR_INDEX.md) · [Verbindlicher Snapshot](MASTER-SNAPSHOT.md) · [Aktuelle Übergabe](docs/PROJEKT_UEBERGABE_2026-10-03_BLOCK89.md) · [Sicherheitsregeln](PROJECT_GUARDRAILS.md)

> Stand: 03.10.2026. Die unten genannten Links verweisen auf vorhandene Dateien oder GitHub-Verzeichnisse. Status bezieht sich auf belegte Funktionen, nicht auf bloß vorhandenen Code. Vor jedem BLOCKRUN tatsächlichen main-HEAD, PRs und Actions erneut prüfen.

## Navigation

| Nr. | Bereich | Direkt öffnen |
|---|---|---|
| 01 | **Architektur & Ablauf** | [Klickbarer Architekturplan](docs/ARCHITEKTUR_INDEX.md) · [Agenten/Übergaben](docs/AGENCY_ORG_AND_HANDOFF.md) |
| 02 | **Zentrale, Aufträge & Orchestrierung** | [Control Center](content_factory_control_center.py) · [Service](content_factory_service.py) · [Auftragszustände](content_factory_core.py) |
| 03 | **Recherche & Fakten** | [Discovery](content_factory_discovery.py) · [Newsroom](content_factory_newsroom.py) · [Quellenregister](config/SOURCE_REGISTRY.md) |
| 04 | **Creative & Redaktion** | [Creative](content_factory_creative.py) · [Schreibprotokoll](config/HUMAN_WRITING_PROTOCOL.md) |
| 05 | **Medienproduktion / Block 6** | [FFmpeg-Handoff](scripts/block6_factory_ffmpeg_handoff.py) · [Media Production](content_factory_media_production.py) · [Video-Dokumentation](docs/VIDEO_SYSTEM.md) |
| 06 | **Audio, Untertitel, Avatar / Block 7** | [AV](content_factory_av.py) · [Whisper-Start](scripts/block7_faster_whisper_startup.py) · [Sprach-Start](scripts/block7_chatterbox_startup.py) |
| 07 | **Vorschau & Neurendern / Block 8** | [Dashboard](infra/ai-central-dashboard/) · [Revision](content_factory_revision_render.py) · [Livetest](scripts/block8_revision_smoke.py) · [Abnahme](docs/BLOCK8_9_REVISION_RENDER_ACCEPTANCE.md) |
| 08 | **Auftragseingang & Publisher / Block 9** | [Control Center](content_factory_control_center.py) · [Shared Inbox](scripts/ai_central_shared_inbox.py) · [R2-Publish-Ledger](content_factory_r2_publish_ledger.py) · [Sicherheitsregeln](docs/PUBLICATION_SAFETY.md) |
| 09 | **Telegram & Freigaben** | [Telegram Router](telegram_router.py) · [Revision-Benachrichtigung](scripts/block89_notify_revision_ready.py) · [Approval](docs/approval/) |
| 10 | **Infrastruktur & KI-Provider** | [Dashboard Worker](infra/ai-central-dashboard/) · [R2 Job Repository](content_factory_r2_job_repository.py) · [Providerkonfiguration](config/llm_providers.json) · [Cloud-Betrieb](docs/CLOUD_AI_CENTRAL_OPERATIONS.md) |
| 11 | **Werkzeuge & Alternativen** | [Einziger verbindlicher Werkzeugindex](docs/TOOL_INDEX.md) · [Guardrails](PROJECT_GUARDRAILS.md) |
| 12 | **Tests, Qualität & GitHub Actions** | [Tests](tests/) · [Workflows](.github/workflows/) · [Block-8-Live-Beweis](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/37117183832) |
| 13 | **Übergaben, Snapshots & Sicherung** | [Aktuelle Übergabe](docs/PROJEKT_UEBERGABE_2026-10-03_BLOCK89.md) · [Aktueller Snapshot](snapshots/SNAPSHOT_2026-10-03_BLOCK89_TELEGRAM_VERIFIED.md) · [Recovery-Branch](https://github.com/Edirne22/KI-SOCIAL-AGENT/tree/backup/2026-10-03-block89-telegram-verified) |

## Jetzt maßgeblich

- **Belegt:** synthetischer FFmpeg-Neurender, private R2-Verifikation, geschützte Vorschau und tatsächlich beim Besitzer eingegangene Telegram-Benachrichtigung. [GitHub-Lauf](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/37117183832).
- **Nächste Abnahme:** Block 9 mit tatsächlichem Dashboard-/Mobil-/Mikrofon-/Upload-/Auftragstest; danach Block 7 mit den persönlichen, autorisierten Audiodateien/Fotos. Kein vollständiger Block-9-E2E-Status allein aus Unit-Tests ableiten.
- **Werkzeuge:** FFmpeg FIRST; OpenChatCut, SupoClip und OmniRoute PAUSED; Chopify ist Ersatzkandidat für SupoClip, **nicht** LIVE. Selora nur vorgemerkte Backup-Idee. [Verbindlicher Werkzeugindex](docs/TOOL_INDEX.md).
- **Sicherheitsgrenze:** keine Veröffentlichung ohne gültige menschliche Einzel-Freigabe; keine neuen Kosten oder privaten Sprachdaten ohne Freigabe.

**Für neue Chat-Sitzungen:** diesen Index → [Architektur](docs/ARCHITEKTUR_INDEX.md) → [aktuellen Snapshot](MASTER-SNAPSHOT.md) → [Guardrails](PROJECT_GUARDRAILS.md) → [Tool-Index](docs/TOOL_INDEX.md) → tatsächliche GitHub-Actions lesen. Historische Roadmaps dürfen die aktuelle FFmpeg-first-Entscheidung nicht überschreiben.
