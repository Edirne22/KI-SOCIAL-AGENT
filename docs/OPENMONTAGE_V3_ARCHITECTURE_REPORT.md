# OpenMontage V3 – Motorsport Video Factory Architecture Report

**Status:** Completed (Block 0 Analysis)
**Target Repository:** `Edirne22/KI-SOCIAL-AGENT`
**Reference Workflow:** OpenMontage V2 Demo (`39081285829`)

---

## 1. Overview & Architectural Principle
OpenMontage V3 establishes an autonomous motorsport video content factory operating as an independent production track inside `KI-SOCIAL-AGENT`.

Key Architectural Mandates:
- **Shared Motorsport Knowledge Base:** Both Instagram/Facebook social publishing and OpenMontage V3 share the exact same checked rosters, scouts, quality filters, source registries, and media license policies.
- **Strict Domain Isolation:** Video jobs, storyboards, manifests, renders, quality logs, and Telegram approval flows maintain complete isolation from daily IG/FB publishing queues. Failures in OpenMontage V3 will never block Instagram/Facebook daily operations.
- **Single Telegram Entrypoint:** Existing `telegram_router.py` handles OpenMontage commands without launching a secondary poller.
- **Publishing Safety:** Video review approval prepares private R2 previews and records editorial decisions. Social publishing is explicitly decoupled and never triggered automatically.

---

## 2. Reusable Infrastructure & Components

### A. Driver, Team & Identity Layer
- `content/MOTOGP_ROSTER.md` & `content/MOTOGP_ROSTER_NEXT.md`: Verified 2026 MotoGP roster (Marc Márquez, Álex Márquez, Francesco Bagnaia, Pedro Acosta, Jorge Martín, Marco Bezzecchi, Fabio Quartararo, Brad Binder, etc.).
- `turkish_rider_names.py`: Turkish rider registry, alias normalization, and accent stripping (Toprak Razgatlıoğlu, Deniz Öncü, Can Öncü, Bahattin Sofuoğlu, Zayn Sofuoğlu).

### B. Research & Sourcing Scouts
- `turkish_riders_scout.py` & `turkish_riders_scout_adapter.py`: Turkish motorsport RSS feeds, news parsing, deduplication.
- `motoetkinlik_source.py`: Turkish motorsport news source adapter (`motoetkinlik.com`).
- `race/race_sources.py`: MotoGP and WorldSBK news sources, official calendar links.
- `config/SOURCE_REGISTRY.md`: Verified source registry mapping official vs supplemental media feeds (`motogp.com`, `worldsbk.com`, `trf1.net`, `tr.motorsport.com`, `motoron.com.tr`, `trmotosports.com`, `motorsport-magazin.com`).

### C. Fact & Quality Management (QM)
- `racing_final_guard.py`: Deterministic last-mile editorial guard and series classification.
- `racing_semantic_qm.py`: Fact checking, entity resolution, and truthfulness assertions.
- `racing_source_claim_guard.py` & `racing_source_entity_guard.py`: Verification of source citations, transfer rumors vs confirmed facts, and event contexts.

### D. Media & Policy Management
- `media_policy.py`: Enforcement of media licensing rules, public domain/fair use constraints, and non-infringing visual fallbacks.
- `config/TRUSTED_MEDIA_SOURCES.json` & `docs/MEDIA_SOURCING.md`: Whitelist of trusted media origins.

### E. Video Rendering & Telegram Router
- `integrations/openmontage/runtime.py` & `integrations/openmontage/creative_renderer.py`: FFmpeg/Remotion scene composer, audio mixing, subtitle rendering, and video assembly.
- `scripts/openmontage_control.py` & `telegram_router.py`: Command routing, state tracking (`memory/OPENMONTAGE_JOBS.json`), Cloudflare R2 preview generation.

---

## 3. Required Modules & Implementation Roadmap

1. **Block 1 – `openmontage_research.py` (Shared Research Adapter):**
   - Converts natural prompt input into structured `research.json`.
   - Aggregates news from existing scouts (`turkish_riders_scout.py`, `motoetkinlik_source.py`, `race/race_sources.py`).
   - Deduplicates items, normalizes driver/team references, tags series/event, and classifies facts vs rumors.

2. **Block 2 – `openmontage_fact_checker.py` (Fact & Recency Guard):**
   - Runs `racing_semantic_qm.py` and `racing_final_guard.py` checks over `research.json`.
   - Rejects outdated items (>7 days for news briefs), unverified transfer rumors, or hallucinated race results (Fail-Closed).

3. **Block 3 – `openmontage_storyboard.py` (Automated Scene Planner):**
   - Maps verified `research.json` into structured `storyboard.json`.
   - Supports 30s, 60s, 90s, 3m, 5m durations; 9:16 (Reels/Shorts) and 16:9 (YouTube) formats; German and Turkish languages.
   - Calculates per-scene timing budgets, dynamic titles, info cards, zoom transitions, and background audio hints.

4. **Block 4 – `openmontage_media_sourcing.py` (Media Manifest Generator):**
   - Constructs `media_manifest.json` with explicit license verification.
   - Applies fallbacks (driver cards, track maps, calendar graphics, animated text, neutral motorsport animations) whenever third-party video rights are unconfirmed.

5. **Block 5 – `openmontage_production.py` (Automated Video Production Engine):**
   - Coordinates `research.json`, `storyboard.json`, and `media_manifest.json` into `integrations/openmontage/creative_renderer.py`.
   - Handles offline TTS voice synth or text/subtitle overlay fallbacks.
   - Performs `ffprobe` technical quality validation on exported MP4s.

6. **Block 6 – Telegram Router Extensions & Job Persistence:**
   - Integrates `/montage erstellen`, `/montage planen`, `/montage status`, `/montage freigeben`, `/montage ablehnen`, `/montage link neu` into `telegram_router.py`.
   - Persists state reliably in `memory/OPENMONTAGE_JOBS.json`.

7. **Block 7 – E2E Integration Suite:**
   - End-to-end unit and integration test suite (`tests/test_openmontage_v3_e2e.py`) validating full pipeline execution without social media publishing side-effects.

---

## 4. Security & Cost Boundaries
- **Zero Paid API Requirement:** Leverages free/local models (NVIDIA NIM/Groq if configured, offline Piper TTS, local FFmpeg/Remotion rendering).
- **No VPS/Container Dependencies:** Runs strictly within existing GitHub Actions runner environments.
- **No Direct Social Publishing:** Approvals only generate private Cloudflare R2 preview links for owner review.
