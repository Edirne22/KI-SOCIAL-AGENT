# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

Stand: 2026-09-19 (Router live, Finanzagent gebaut)

## ✅ Erledigt (gemergt und live)

### Telegram-Stack (komplett saniert)
- P0 – Exit-2-Crash behoben
- P1 – Queue atomar (ein Update pro Lauf)
- P2 – Concurrency entkoppelt
- Parser-Robustheit (fehlende Posts blockieren nicht mehr)
- active_batch_id-Fix (PR #17)
- Workflow-Persistenz (`git add -A`)
- Workflow-Env um alle 5 Router-Keys erweitert
- End-to-End-Test MotoGP → Instagram + Facebook erfolgreich

### Doku & Werkzeuge
- P3 – Gemini-Inventur (`docs/GEMINI_INVENTORY.md`)
- P4 – V8.6-Promotionsplan (`docs/V8.6_PROMOTION_PLAN.md`)
- Race-Calendar-Pipeline V4 (6 Fixes + Review-Korrekturen)
- `AGENTS.md` (Jules-Regeln + i-have-adhd)
- `llm-router-test.yml` (isolierter Router-Smoketest)

### Multi-Modell-Router (live)
- `llm_router.py` + `config/llm_providers.json`
- 5 Anbieter mit Auto-Fallback: Groq, Google, OpenRouter, NVIDIA, Cloudflare
- Cooldown bei 429, Retry-After-Beachtung
- Skip-Logik bei fehlendem Key
- Config-Validierung, max_tokens=2000
- **Alle 3 Router-Tests grün**

### Agenten auf Router (7)
- ✅ `follow_analyzer.py`
- ✅ `deal_hunter.py` (search_provider)
- ✅ `search_provider.py`
- ✅ `inspiration/orchestrator.py`
- ✅ `weekly_plan.py` (getestet)
- ✅ `ride_with_me.py` (getestet)
- ✅ `generate_ideas.py` (getestet)

### Finanzagent (Agent 15)
- ✅ `finance_planner.py` + Workflow + 5 memory-Dateien
- ✅ Cron: Montag 07:00 UTC
- ⚠️ **Analyse aktuell leer** (nur „User Safety: safe") – Fix nötig

### Secrets in GitHub
`GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `NVIDIA_API_KEY` (neu), `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `APIFY_API_TOKEN`

## 🔴 AKUT OFFEN – sofort

| # | Aufgabe | Auftrag liegt bereit? |
|---|---|---|
| 1 | **Finanzagent-Fix** (Groq primär + Safety-Schutz) | ✅ ja, in Jules rausschicken |
| 2 | `followed_accounts.md` Header korrigieren (Mo/Mi/Fr) | nein, manuell |
| 3 | Watchlist-Tracker für Handy-Tracking bauen | ja, als Auftrag formulierbar |

## 🟠 NVIDIA-Modelle einbinden (bald)

### Text-to-Image
| Modell | Calls/30d |
|---|---|
| `black-forest-labs/flux.2-klein-4b` | 338K |
| `black-forest-labs/flux.1-dev` | 303K |
| `black-forest-labs/flux.1-schnell` | 227K |
| `black-forest-labs/flux.1-kontext-dev` | 7K |
| `stabilityai/stable-diffusion-3.5-large` | – |
| `qwen/qwen-image` | – |

**Empfehlung:** `image_router.py` → FLUX.1-schnell primär, FLUX.1-dev Fallback, Agnes letzter Fallback.

### Vision / Image-to-Text
- `meta/llama-3.2-11b-vision-instruct`
- `meta/llama-3.2-90b-vision-instruct`
- `moonshotai/kimi-k3` (multimodal)
- `nvidia/nemotron-3-nano-omni` (Bild+Video+Speech+Text)
- `nvidia/nemotron-ocr-v2`
- `google/paligemma`

### Video
- `nvidia/cosmos3-nano` (Video-Generierung)
- `nvidia/cosmos3-nano-reasoner`
- `nvidia/video-super-resolution`
- `nvidia/relighting`
- `nvidia/active-speaker-detection`
- `nvidia/synthetic-video-detector`

### Speech / Audio
- NVIDIA Speech-to-Text (mehrere Modelle)
- NVIDIA Text-to-Speech (Riva)

### Übersetzung
- NVIDIA Translation (37/36/12 Sprachen) → für DE ↔ TR

### LLM (Router-Erweiterung)
- `meta/llama-3.3-70b-instruct`
- `google/gemma-4-31b-it`
- `nvidia/nemotron-3-ultra-550b`
- `nvidia/nemotron-3.5-lightning-30b`

### Embedding / Safety
- `nvidia/embedding-1b` (RAG/Memory)
- `nvidia/nemotron-3.5-content-safety` (Post-Qualität)

### ❌ Nicht relevant
- ARC / Evo 2 (Biologie)
- Drug Discovery
- Route Optimization (cuOpt)

### Technische Notizen NVIDIA NIM
- **Text-API:** `https://integrate.api.nvidia.com/v1` (OpenAI-kompatibel)
- **Bild-API:** `https://ai.api.nvidia.com/v1/genai/<model>` (eigenes Format)
- **40 RPM, kostenlos, kein Token-Billing**

## 🟡 Qualitäts-Fixes (offen)

| # | Was |
|---|---|
| 4 | Serie-Filter (Formel 1 → kein Bike-Block) |
| 5 | Agnes-Story strenger (erfundene Namen) |
| 6 | Deal-Hunter Transparenz (Provider-Anzeige) |
| 7 | Cloudflare-Bildgenerierung (FLUX + Leonardo) |
| 8 | Publisher-Workflow `git add -A` (Insta + FB) |
| 9 | Kimi K3 testen + in NVIDIA-Config aktivieren |

## 🟢 Nach VPS-Setup

| # | Was |
|---|---|
| 10 | VPS einrichten (Ubuntu 24.04) |
| 11 | SearXNG (kostenlose Websuche) |
| 12 | OmniRoute |
| 13 | `speech_router.py` (TTS + STT) |
| 14 | `translation_router.py` (DE ↔ TR) |
| 15 | `video_router.py` (Cosmos3 Nano) |
| 16 | Remotion + Video-Pipeline |

## 🟣 Strategisch

| # | Was |
|---|---|
| 17 | V8.6 Promotion Debug → main |
| 18 | Debug-Workflow-Split auflösen |
| 19 | Autonome Content-Fabrik (Vision) |

## 🎯 Vision

Autonome Content-Fabrik: Agenten erstellen aus einem Prompt selbstständig Videos, Bilder und Texte. OmniRoute bündelt alle KI-Anbieter. Remotion rendert Videos. KI-Video-Modelle liefern Rohmaterial. Kinocut schneidet. Agent gibt Prompt → fertiger Reel.

## 🧰 Router-Architektur (live)

| Task-Typ | Reihenfolge |
|---|---|
| `fast_chat` | Groq → Google → NVIDIA |
| `reasoning` | OpenRouter → Google → NVIDIA |
| `coding` | OpenRouter → NVIDIA → Groq |
| `long_context` | NVIDIA → OpenRouter → Google |
| `default` | Groq → Google → OpenRouter → NVIDIA → Cloudflare |

### Tote Modelle (nicht verwenden)
- `deepseek/deepseek-r1:free` (nicht mehr kostenlos)
- `deepseek-ai/deepseek-v4-pro` (EOL 07.08.2026)
- `deepseek-ai/deepseek-v4-flash` (EOL 07.08.2026)
- `gemini-2.5-flash` (nur Bestandsnutzer)

## 🧾 Apify-Kosten

| Agent | Läuft | Apify |
|---|---|---|
| Follow-Analyzer | Mo/Mi/Fr | bis 8 Accounts |
| Deal-Hunter | manuell / Telegram | 1 Query |
| Watchlist | nicht automatisch | – |

**Follow-Analyzer = Kostentreiber.** Frequenz senken oder VPS + SearXNG.

## ⚠️ Kritische Regeln

- Jules: max 3 Sessions, max 15 Credits/Tag
- Debug-Branch: nicht anfassen
- Kein Auto-Merge, kein Auto-Publish
- Secrets nur notieren, nie committen
- NVIDIA-Key läuft 18.03.2027 ab
- Router-Config nur direkt auf `main` pflegen

## 📎 Links

- Repo: https://github.com/Edirne22/KI-SOCIAL-AGENT
- Actions: https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- Handbuch: docs/HANDBUCH.md
- Gemini-Inventur: docs/GEMINI_INVENTORY.md
- V8.6-Plan: docs/V8.6_PROMOTION_PLAN.md
- Agenten-Regeln: AGENTS.md
- Router-Test: Actions → LLM Router Test
- NVIDIA Models: https://build.nvidia.com/models

## 📝 Für neue Chats

Poste den Inhalt dieser Datei, dann ist der Assistent sofort auf Stand.
