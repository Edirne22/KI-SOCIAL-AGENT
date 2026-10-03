# Edirne22 — aktuelle Systemarchitektur (anklickbar)

[Zurück zum Gesamtindex](../INDEX.md) · [Projektübergabe](PROJEKT_UEBERGABE_2026-10-03_BLOCK89.md) · [Sicherheitsregeln](../PROJECT_GUARDRAILS.md)

## Architektur vom Auftrag bis zur Freigabe

```text
Besitzer: Dashboard / Telegram / autorisierter Medien-Upload
      ↓
[01] AUTHENTIFIZIERTER EINGANG + AUFTRAG
      ↓
[02] PRODUKTIONSLEITUNG + JOB-STATUS / PRIVATE PERSISTENZ
      ↓
[03] DISCOVERY + NEWSROOM / SOURCE-FACT
      ↓
[04] CREATIVE + REDAKTION
      ↓
[05] MEDIEN: FFMPEG-FIRST → PRIVATES R2
      ↓
[06] AUDIO / UNTERTITEL / AVATAR (BLOCK 7: ABNAHME OFFEN)
      ↓
[07] FINAL QM / GOLDEN TABLET / REVISIONSGEBUNDENE VORSCHAU
      ↓
[08] DASHBOARD + TELEGRAM: ÄNDERN / VERWERFEN / FREIGEBEN
      ↓
[09] PUBLISHER: NUR NACH GÜLTIGER MENSCHLICHER FREIGABE
```

| Schritt | Funktion | Implementierung / Details | Aktuelle Abnahmegrenze |
|---|---|---|---|
| 01 | Dashboard, Upload, Mikrofon, Telegram | [Dashboard UI](../infra/ai-central-dashboard/public/index.html), [Worker](../infra/ai-central-dashboard/src/index.js), [Telegram](../telegram_router.py), [Shared Inbox](../scripts/ai_central_shared_inbox.py) | Reale Besitzer-Eingabe und Mikrofon-Abnahme offen |
| 02 | Produktionsleitung, Ressourcen, Auftragszustände | [Core](../content_factory_core.py), [Control Center](../content_factory_control_center.py), [Resource Manager](../content_factory_local_resource_manager.py), [persistenter Service](../content_factory_persistent_service.py), [R2 Repository](../content_factory_r2_job_repository.py) | Einzelkomponenten vorhanden; komplette Live-Staffel separat prüfen |
| 03 | Recherche, Quellen und Fakten | [Discovery](../content_factory_discovery.py), [Newsroom](../content_factory_newsroom.py), [Quellen](../config/SOURCE_REGISTRY.md), [Faktenkarte](RACING_EVIDENCE_MAP.md) | Keine synthetischen Aussagen als verifizierte Fakten behandeln |
| 04 | Redaktion und Tonalität | [Creative](../content_factory_creative.py), [Schreibprotokoll](../config/HUMAN_WRITING_PROTOCOL.md) | Redaktionelle Prüfung bleibt nötig |
| 05 | Video, Medien und private Speicherung | [Media Production](../content_factory_media_production.py), [FFmpeg-Handoff](../scripts/block6_factory_ffmpeg_handoff.py), [Medienadapter](../content_factory_adapters.py), [Video-System](VIDEO_SYSTEM.md) | FFmpeg/R2-Testpfad belegt; keine OpenChatCut-Abhängigkeit |
| 06 | Sprache, Transkript, Untertitel | [AV](../content_factory_av.py), [private ASR](../content_factory_private_asr.py), [ASR Runtime](../content_factory_private_asr_runtime.py), [Whisper-Start](../scripts/block7_faster_whisper_startup.py) | Block 7 Besitzer-Audio und DE/TR-Abnahme offen |
| 07 | QM, private Vorschau, automatisches Neurendern | [Golden Tablet](../content_factory_golden_tablet.py), [Golden Media](../content_factory_golden_media.py), [Preview](../content_factory_dashboard_preview.py), [Revision](../content_factory_revision_render.py), [Review ACK](../content_factory_dashboard_review_ack.py) | Synthetischer R2/Telegram-Livetest erfolgreich; echte Besitzer-Vorschau separat |
| 08 | Freigaben und Nachrichten | [Telegram-Nachricht](../scripts/block89_notify_revision_ready.py), [Review Applier](../content_factory_dashboard_review_applier.py), [Approval UI](approval/), [Block-8/9-Abnahme](BLOCK8_9_REVISION_RENDER_ACCEPTANCE.md) | Kein automatisches Posten |
| 09 | Sichere Plattformübergabe | [Publisher Ledger](../content_factory_publish_ledger.py), [R2 Ledger](../content_factory_r2_publish_ledger.py), [Meta Delivery](../content_factory_meta_private_delivery.py), [Publikationssicherheit](PUBLICATION_SAFETY.md) | Reale Plattform-Receipt-E2E nur nach konkreter Human-Freigabe |

## Betrieb und Sicherheitsgrenzen

- **Code und CI:** [GitHub Actions](../.github/workflows/), [Tests](../tests/), [Block8/9 Erfolgsbeleg](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/37117183832).
- **Dashboard:** [Worker-Konfiguration](../infra/ai-central-dashboard/wrangler.jsonc), [Dashboard-Tests](../infra/ai-central-dashboard/tests/). Cloudflare Worker ist Eingang/Steuerung; R2 ist privater Objektspeicher, **keine** Rechenmaschine.
- **KI-Provider:** [Providerkonfiguration](../config/llm_providers.json), [Model Router](../config/model_router.json), [Budgetregeln](AI_CENTRAL_TEAM_TOKEN_BUDGET_V1.md). Konfiguration bedeutet nicht automatisch aktuelle Verfügbarkeit.
- **Werkzeugentscheidung:** [TOOL_INDEX.md](TOOL_INDEX.md). FFmpeg FIRST, Remotion optional; OpenChatCut/SupoClip PAUSED, Chopify RESEARCH_ONLY, OmniRoute PAUSED, Selora nur Backup-Idee.
- **Wiederherstellung:** [Aktuelle Übergabe](PROJEKT_UEBERGABE_2026-10-03_BLOCK89.md), [Snapshot](../snapshots/SNAPSHOT_2026-10-03_BLOCK89_TELEGRAM_VERIFIED.md), [exakter Git-Backup-Branch](https://github.com/Edirne22/KI-SOCIAL-AGENT/tree/backup/2026-10-03-block89-telegram-verified). Cloudflare-Secrets, private R2-Medien und Laufzeitkonfiguration sind nicht im Git-Backup enthalten.

**Keine falsche Vollständigkeit:** Ein Link belegt die Existenz einer Implementierung oder Dokumentation, nicht automatisch eine vollständige Live-Abnahme. Für den aktuellen Beweisstatus immer die Projektübergabe und Actions lesen.
