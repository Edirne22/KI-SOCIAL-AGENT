# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-19
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT

---

## 🏍️ BÜLENTS CONTENT-VISION (dauerhaft)

### Person & Nische
- Bülent, 50, fährt seit 1992 Motorrad
- Maschine: BMW M1000R, Baujahr 2024
- Region: Ruhrgebiet + Sauerland
- Hausstrecke: Radevormwald → Biggesee → Sägewerk
- Handle: @edirnelibuelent

### Ziel
Aus der Fabrik raus. Eigene KI-Agentur. Content, der autonom läuft.
Einnahmen: Sponsoren + Agentur-Kunden.
Zeitachse: 12–24 Monate.

### Content-Säulen
1. **Strecken-Doku** – konkrete Strecken, Kurven, Tracks (Ruhrgebiet)
2. **M1000R-Realität** – ehrliche Berichte (Kosten, Wartung, Erfahrung)
3. **Community** – gemeinsame Touren ab Radevormwald
4. **Biker-Alltag** – Generationen-Content, echte Geschichten

### Format
- Reels: 30–60 Sek, Hook in ersten 3 Sek, immer Untertitel
- Echte Fotos/Videos (kein KI-Editorial für Personenfotos)
- 1 Reel/Tag (Monat 1–6), 2–3/Tag (ab Monat 6)

### Schlachtplan
- **Woche 1:** Setup (Handle, Bio, Profilbild) + 2 Reels
- **Monat 1:** 30 Reels, erste Zahlen
- **Monat 6:** 5.000 Follower, erste Kooperationen (100–500 €/Monat)
- **Monat 12:** 20.000 Follower, 2.500–3.500 €/Monat → Kündigung prüfen
- **Monat 24:** 50.000+ Follower, 10.000 €/Monat → Fabrik gekündigt

### Nächster konkreter Schritt
1. Instagram-Handle prüfen + Bio schreiben
2. Profilbild: Bülent + M1000R
3. Erste Fahrt mit Handy-Video (Radevormwald → Biggesee)
4. Ersten Reel bauen (CapCut, kostenlos)
5. Ersten Reel posten

### KI-Agenten unterstützen später
- MotoGP-Agent → Text für Posts
- NVIDIA Image-Router → Grafiken/Infografiken
- NVIDIA Speech-to-Text → Untertitel automatisch
- NVIDIA TTS → Voiceover
- Remotion + VPS → Video-Pipeline autonom
- OmniRoute → alles gebündelt

### Antrieb
Kinder. Für sie da sein. Ihnen ein besseres Leben ermöglichen.

---

## 🤖 NVIDIA NIM – Merkliste (Einbau-Plan)

### Technische Details
| Aspekt | Wert |
|---|---|
| Text-API | `https://integrate.api.nvidia.com/v1` (OpenAI-kompatibel) |
| Bild-API | `https://ai.api.nvidia.com/v1/genai/<model>` (eigenes Format) |
| Rate-Limit | 40 Requests/Minute |
| Kosten | Kostenlos zum Prototyping |
| Token-Billing | Keins |
| API-Key | `NVIDIA_API_KEY` (Ablauf 18.03.2027) |

### 🔴 Priorität 1 – Sofort einbauen

**Text/Reasoning:**
- `moonshotai/kimi-k3` → in `config/llm_providers.json` nvidia.models (reasoning, coding, long_context) — ✅ ERLEDIGT 19.09.2026
- Grund: 1M Kontext, Top-Reasoning, Coding, multimodal. Ersetzt `deepseek-v4-flash` (EOL).

**Bildgenerierung → neuer `image_router.py`:**
- Primär: `black-forest-labs/flux.1-schnell`
- Fallback 1: `black-forest-labs/flux.1-dev`
- Fallback 2: `black-forest-labs/flux.2-klein-4b`
- Letzter Fallback: Agnes (bestehend)

### 🟡 Priorität 2 – Nach image_router.py

**Vision → neuer `vision_router.py`:**
- `meta/llama-3.2-11b-vision-instruct` → Instagram-Bilder analysieren
- `nvidia/nemotron-ocr-v2` → Text aus Bildern (Finanzagent-Tabellen)
- `nvidia/nemotron-3-nano-omni` → Multimodal (Bild+Video+Speech+Text)

**Übersetzung → neuer `translation_router.py`:**
- Riva Translate 1.6b → DE ↔ TR (36 Sprachen)

**Speech → neuer `speech_router.py` (nach VPS):**
- Nemotron ASR Streaming → Untertitel für Reels
- Magpie TTS Multilingual → Voiceover (12 Sprachen)

### 🟢 Priorität 3 – Nach VPS

**Video → neuer `video_router.py`:**
- `nvidia/cosmos3-nano` → Video-Generierung
- `nvidia/cosmos-transfer2.5-2b` → Video-zu-Video
- `nvidia/cosmos3-nano-reasoner` → Video/Bild-Verständnis
- `nvidia/video-super-resolution` → Videos hochskalieren
- `nvidia/relighting` → Beleuchtung anpassen

**Embedding:**
- `nvidia/nemotron-3-embed-1b` → Memory-Suche, RAG (34 Sprachen)

**Safety:**
- `nvidia/nemotron-3-content-safety` → Post-Qualität prüfen

**Router-Erweiterung (mehr Optionen):**
- `nvidia/nemotron-3-ultra-550b` → 1M Kontext, agentic
- `nvidia/nemotron-3-super-120b` → Effizienter MoE
- `nvidia/nemotron-3.5-lightning-30b` → Schnelle Agenten
- `meta/llama-3.3-70b-instruct` → Standard-LLM
- `google/gemma-3-27b` → Reasoning/Coding
- `minimaxai/minimax-m3` → Multimodal MoE (ist drin)
- `zai/glm-5.2` → Agentic + Coding

### ❌ Nicht relevant
- ARC / Evo 2 (Biologie)
- Drug Discovery
- Route Optimization (cuOpt)

### 🎯 Geplante Router-Module
| Modul | Primär | Fallback | Status |
|---|---|---|---|
| `llm_router.py` | Groq/OpenRouter/Google/NVIDIA/Cloudflare | – | ✅ fertig |
| `image_router.py` | FLUX.1-schnell | FLUX.1-dev → FLUX.2-klein-4b → Agnes | 🔄 in Arbeit |
| `vision_router.py` | Llama Vision | Kimi K3 → Nemotron OCR | 🔴 offen |
| `translation_router.py` | Riva Translate | – | 🔴 offen |
| `speech_router.py` | Nemotron ASR + Magpie TTS | – | 🟢 nach VPS |
| `video_router.py` | Cosmos3 Nano | – | 🟢 nach VPS |

---

## 📋 AKTUELLER STAND (19.09.2026)

### ✅ HEUTE ERLEDIGT

**NVIDIA-Integration – Basis**
- ✅ Kimi K3 in `config/llm_providers.json` (PR #29 + #30 gemergt)
  - `reasoning`, `coding`, `long_context`, `multimodal` → `moonshotai/kimi-k3`
  - `ocr` → `nvidia/nemotron-ocr-v2`
  - `default` → `minimaxai/minimax-m3` (unverändert)
  - `deepseek-v4-flash` komplett entfernt
- ✅ Kimi K3 Testcall – HTTP 200, `model=moonshotai/kimi-k3`, läuft
- ✅ `NVIDIA_API_KEY` in Workflows verdrahtet (daily-ideas, deal-hunter, ride-with-me, weekly-plan)
- ✅ Test-Workflow `test-image-router.yml` angelegt (wartet auf `image_router.py`)

**Content-Setup Bülent**
- ✅ Instagram Bio
- ✅ Facebook Bio + Kategorie
- ✅ Content-Vision + Schlachtplan (24 Monate) dokumentiert
- ✅ 10 Bikertreffs dokumentiert (`config/Bikertreffs.md`)

**Doku**
- ✅ `docs/HANDBUCH.md`
- ✅ `docs/PROJEKT_UEBERGABE.md`
- ✅ `docs/GEMINI_INVENTORY.md`
- ✅ `docs/V8.6_PROMOTION_PLAN.md`

**Aus Vortagen (17.09. + früher)**
- ✅ Telegram-Stack P0–P2 + Parser + Batch-ID
- ✅ `llm_router.py` + 5 Provider (Groq, Google, OpenRouter, NVIDIA, Cloudflare)
- ✅ Finanzagent (Agent 15) – läuft über Groq, Cron Mo 07:00 UTC
- ✅ Race-Calendar V4 (grün)
- ✅ Instagram + Facebook Publisher
- ✅ Remotion-Video gerendert
- ✅ Deal-Hunter-Fix
- ✅ eBay Developer Account

### 🔄 LÄUFT GERADE

- 🔄 **Jules-Session: `image_router.py` + `test_image_router.py`**
  - Zweiter Versuch (erster ist fehlgeschlagen)
  - Neuer Chat, verbesserter Prompt mit Root-Pfad-Betonung
  - Erwartung: PR mit 2 neuen Dateien
  - Status: ⏳ warte auf PR-Link

---

## 🔴 OFFEN – PRIORITÄT 1 (diese Woche)

### A) NVIDIA-Router-Module

- 🔴 **`image_router.py`** (läuft gerade)
  - Primär: `flux.1-schnell`
  - Fallback 1: `flux.1-dev`
  - Fallback 2: `flux.2-klein-4b`
  - Letzter Fallback: `agnes_generate_image()` aus `generate_agnes_media.py`
  - ENV: `NVIDIA_IMAGE_API_STYLE` = `genai` | `openai`
  - Nach PR: merge + Smoke-Test über `test-image-router.yml`

- 🔴 **`vision_router.py`** (nach `image_router`)
  - `general` → `meta/llama-3.2-11b-vision-instruct` (Fallback: Kimi K3)
  - `ocr` → `nvidia/nemotron-ocr-v2`
  - `omni` → `nvidia/nemotron-3-nano-omni`
  - Zweck: Instagram-Bilder analysieren + Finanzagent-Tabellen

- 🔴 **`translation_router.py`** (nach `vision_router`)
  - `Riva Translate 1.6b` → DE ↔ TR (36 Sprachen)
  - Fallback: `llm_router` mit Übersetzungs-Prompt

### B) Content Bülent

- 🔴 Erster Reel „10 Bikertreffs" – bauen + posten (1 Std)
- 🔴 `followed_accounts.md` Header korrigieren (Mo/Mi/Fr, 5 Min)

### C) Doku-Aufräumen

- 🔴 `docs/PROJEKT_UEBERGABE.md` – letzten `deepseek-v4-flash`-Rest entfernen

---

## 🟡 OFFEN – PRIORITÄT 2 (2 Wochen)

- 🟡 Memory-Embedding → `nvidia/nemotron-3-embed-1b` (34 Sprachen)
- 🟡 Safety-Check → `nvidia/nemotron-3-content-safety` (Post-Qualität)
- 🟡 Router-Erweiterung (`enabled: false` als Vormerkung):
  - `nvidia/nemotron-3-ultra-550b` (1M Kontext, agentic)
  - `nvidia/nemotron-3-super-120b` (MoE)
  - `nvidia/nemotron-3.5-lightning-30b` (schnelle Agenten)
  - `zai/glm-5.2` (Agentic + Coding)
  - `google/gemma-3-27b` (Reasoning/Coding)
  - `meta/llama-3.3-70b-instruct` (Standard-LLM)
- 🟡 Watchlist-Tracker für Handy-Tracking
- 🟡 Serie-Filter Rennkalender (Formel 1 raus)
- 🟡 Agnes-Story strenger (erfundene Namen vermeiden)
- 🟡 Deal-Hunter Transparenz (Provider-Anzeige)
- 🟡 Cloudflare-Bilder (FLUX + Leonardo)
- 🟡 Publisher-Workflow `git add -A`
- 🟡 Debug-Branch-Schutz (Branch-Protection + Workflow-Filter)
- 🟡 Memory-Trennung für OpenCode (`.opencodeignore`)

---

## 🟢 OFFEN – NACH VPS

- 🟢 VPS einrichten (Ubuntu 24.04)
- 🟢 SearXNG installieren
- 🟢 OmniRoute installieren
- 🟢 `speech_router.py`
  - `nvidia/nemotron-asr-streaming` → Untertitel für Reels
  - `nvidia/magpie-tts-multilingual` → Voiceover (12 Sprachen)
- 🟢 `video_router.py`
  - `nvidia/cosmos3-nano` → Text→Video / Bild→Video
  - `nvidia/cosmos-transfer2.5-2b` → Video-zu-Video
  - `nvidia/cosmos3-nano-reasoner` → Video/Bild-Verständnis
  - `nvidia/video-super-resolution` → Upscaling
  - `nvidia/relighting` → Beleuchtung
- 🟢 Objekterkennung/Tabellen
  - `nvidia/nemo-retriever-page-elements-v3`
  - Table Structure NIM
- 🟢 Remotion + Video-Pipeline autonom

---

## 🟣 STRATEGISCH

- 🟣 V8.6 Promotion Debug → main
- 🟣 Debug-Workflow-Split auflösen
- 🟣 OpenRouter 10 $ aufladen (nach Beobachtung, für 1.000 Anfragen/Tag)
- 🟣 Autonome Content-Fabrik (Vision)

---

## ⚠️ WICHTIGE HINWEISE

### NVIDIA-API-Key
- Ablauf: **18.03.2027** → Reminder anlegen
- Rate-Limit: **40 RPM** (kostenlos)
- Kein Token-Billing

### DeepSeek bei NVIDIA
- `deepseek-v4-flash-0731` wird am **22.09.2026 abgeschaltet**
- Kein Nachfolger in Sicht → nicht mehr einplanen

### Bild-API-Formate
- Legacy: `ai.api.nvidia.com/v1/genai/<model>` (eigenes Format)
- Neu: `integrate.api.nvidia.com/v1/images/generations` (OpenAI-kompatibel)
- Umgeschaltet via `NVIDIA_IMAGE_API_STYLE`

### Jules-Regeln
- Max **3 parallele Sessions**
- Max **15 Credits/Tag**
- Reset: **~02:00 deutscher Zeit** (00:00 UTC)
- **Neuer Auftrag = neuer Chat**
- Fix an gemergtem PR = neuer Chat

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

### Telegram
- ✅ Router-Fix erledigt → Telegram funktioniert wieder normal

---

## 📊 CREDIT-STAND

- Verbraucht heute: **~10–11 von 15**
- Übrig: **~4–5**
- Reset: **~02:00 Uhr deutscher Zeit**
- Geplant für heute: `image_router.py` (1–2 Credits)

---

## 🎯 NÄCHSTE 3 TAGE

### Tag 1 (heute, 19.09.)
- ⏳ `image_router.py` PR abwarten → merge → Smoke-Test
- 📄 `PROJEKT_UEBERGABE.md` aufräumen

### Tag 2 (morgen, 20.09.)
- 🚀 `vision_router.py` (Jules, 1 Credit)
- 🚀 `translation_router.py` (Jules, 1 Credit)
- 🎬 Erster Reel „10 Bikertreffs" bauen

### Tag 3 (21.09.)
- 🧠 Memory-Embedding einbinden (Jules, 1 Credit)
- ⚙️ Router-Erweiterung (Config-Only, Jules, 1 Credit)
- 📊 Erste Zahlen aus Instagram/Facebook analysieren

---

## 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **PRs:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **Handbuch:** `docs/HANDBUCH.md`
- **Übergabe:** `docs/PROJEKT_UEBERGABE.md`
- **NVIDIA Build:** https://build.nvidia.com/models

## 🖥️ Approval-Dashboard (geplant)

**Ziel:** Web-Oberfläche zur Freigabe von Content-Entwürfen.
**Aktuell:** Freigabe läuft über Telegram.

### Stufe 1 – HEUTE
- ✅ Telegram-Approval (läuft)

### Stufe 2 – KURZFRISTIG (1–2 Wochen)
- **Technik:** GitHub Pages, statische HTML-Seite
- **Datenquelle:** `docs/approval/queue.json` (vom Agent geschrieben)
- **Vorschau:** Bilder aus `assets/pending/`
- **Freigabe:** Button → `workflow_dispatch` → Publisher
- **Auth:** GitHub-Login
- **Kosten:** 0 €
- **Aufwand:** 1 Jules-Credit
- **URL:** `edirne22.github.io/KI-SOCIAL-AGENT/`

### Stufe 3 – NACH VPS (1–3 Monate)
- **Stack:** Streamlit oder Next.js
- **Features:** Kalender, Analytics, Content-Bibliothek, Multi-Account
- **Aufwand:** 3–5 Jules-Tasks

---

## 📸 SNAPSHOT – 19.09.2026 (Ende Tag 1)

### ✅ HEUTE ERLEDIGT

**NVIDIA-Basis**
- ✅ Kimi K3 in `config/llm_providers.json` (PR #29 + #30)
  - `reasoning`, `coding`, `long_context`, `multimodal` → `moonshotai/kimi-k3`
  - `ocr` → `nvidia/nemotron-ocr-v2`
  - `default` → `minimaxai/minimax-m3`
  - `deepseek-v4-flash` entfernt (EOL 22.09.2026)
- ✅ Kimi K3 Testcall: HTTP 200, funktioniert
- ✅ `NVIDIA_API_KEY` in Workflows verdrahtet

**`image_router.py` (Priorität 1)**
- ✅ Erstellt + gemergt (2. Versuch, mit Root-Pfad-Fix)
- ✅ Bug-Fix 1: FLUX-Parameter pro Modell (schnell: steps=4 ohne cfg_scale/mode; dev: steps=50 mit mode=""/image=""/cfg_scale=5)
- ✅ Bug-Fix 2: klein-4b aus Kette entfernt (Image-Editing, kein Text-zu-Bild)
- ✅ Bug-Fix 3: Timeout 60 → 180s
- ✅ Bug-Fix 4: Retry-Schleife entfernt (NVIDIA Free-Tier = 25 Requests/Monat)
- ⏳ **Finaler Test läuft** (Actions → Test Image Router)

**NVIDIA-Wissensbasis**
- ✅ Free-Tier: 25 Requests/Monat pro Modell (nicht pro Tag)
- ✅ „Using free API for development" = nutzbar
- ✅ „Downloadable" = meist kein Free-Endpoint
- ✅ „Upgrade" = kostenpflichtig → nicht klicken
- ✅ Endpoints:
  - Text/Vision: `https://integrate.api.nvidia.com/v1` (OpenAI-kompatibel)
  - Bild (GenAI): `https://ai.api.nvidia.com/v1/genai/<model>` (eigenes Format)

**API-Key-Verwaltung**
- ✅ Alter Key (versehentlich gepostet) gelöscht
- ✅ Neuer Key `KI-SOCIAL-AGENT-v2` in GitHub Secrets (`NVIDIA_API_KEY`)
- ✅ Zweiter Key `NVIDIABuild-Autogen-65` gelöscht (sauber)
- ✅ Keine offenen Sicherheitslücken

**Doku**
- ✅ `docs/PROJEKT_UEBERGABE.md` komplett neu strukturiert
  - BÜLENTS CONTENT-VISION
  - NVIDIA NIM Merkliste
  - Aktueller Stand
  - Wichtige Hinweise
  - Quellen & Links

---

### 🔄 LÄUFT GERADE

**Test Image Router**
- Actions → „Test Image Router" → Run workflow
- Ziel: `image_router: generated via flux.1-schnell`
- Fallback-Erfolg: `generated via flux.1-dev` (auch okay)
- Worst Case: `NVIDIA chain exhausted, using Agnes` (immer noch grün, aber kein NVIDIA)

**Sobald Test fertig:** Log an Assistenten → Auswertung

---

### 🔴 OFFEN – PRIORITÄT 1 (nächste Tage)

**NVIDIA-Router (Reihenfolge zwingend)**
- 🔴 `vision_router.py` (nach image_router)
  - `general` → `meta/llama-3.2-11b-vision-instruct` (Fallback: Kimi K3)
  - `ocr` → `nvidia/nemotron-ocr-v2`
  - `omni` → `nvidia/nemotron-3-nano-omni`
  - Zweck: Instagram-Bilder analysieren + Finanzagent-Tabellen
- 🔴 `translation_router.py`
  - `Riva Translate 1.6b` → DE ↔ TR (36 Sprachen)
  - Fallback: `llm_router` mit Übersetzungs-Prompt

**Content Bülent**
- 🔴 Erster Reel „10 Bikertreffs" – bauen + posten (1 Std, manuell)
- 🔴 `followed_accounts.md` Header korrigieren (Mo/Mi/Fr)

---

### 🟡 OFFEN – PRIORITÄT 2 (2 Wochen)

- 🟡 Memory-Embedding → `nvidia/nemotron-3-embed-1b`
- 🟡 Safety-Check → `nvidia/nemotron-3-content-safety`
- 🟡 Router-Erweiterung in `config/llm_providers.json` (Reserve-Modelle):
  - `nvidia/nemotron-3.5-lightning-30b-a3b`
  - `z-ai/glm-5-3`
  - `google/gemma-4-31b-it`
  - `meta/muse-glimmer-30b`
  - `nvidia/nemotron-3-super-120b`
  - `nvidia/nemotron-3-ultra-550b`
  - `qwen/qwen-image-edit`
- 🟡 Watchlist-Tracker
- 🟡 Serie-Filter Rennkalender
- 🟡 Agnes-Story strenger
- 🟡 Deal-Hunter Transparenz
- 🟡 Cloudflare-Bilder (FLUX + Leonardo)
- 🟡 Publisher-Workflow `git add -A`
- 🟡 Debug-Branch-Schutz
- 🟡 Memory-Trennung (`.opencodeignore`)

---

### 🖥️ APPROVAL-DASHBOARD (geplant)

**Stufe 1 – HEUTE:** ✅ Telegram-Approval (läuft)

**Stufe 2 – KURZFRISTIG (1–2 Wochen):**
- **Technik:** GitHub Pages, statische HTML
- **Datenquelle:** `docs/approval/queue.json`
- **Vorschau:** Bilder aus `assets/pending/`
- **Freigabe:** Button → `workflow_dispatch` → Publisher
- **Auth:** GitHub-Login
- **Kosten:** 0 €
- **Aufwand:** 1 Jules-Credit
- **URL:** `edirne22.github.io/KI-SOCIAL-AGENT/`

**Stufe 3 – NACH VPS (1–3 Monate):**
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek, Multi-Account

---

### 📦 CLAWHUB-SKILLS (Social-Media-Automatisierung)

**Empfohlen:**
- **Phy Social Post** → Primär (Insta + FB + TikTok)
  - `openclaw skills install @phy041/phy-social-post`
- **Multi-Platform Scheduler** → Content-Kalender
- **Outfeed** → Bulk-Publishing (25 Drafts)

**Mit Vorsicht:**
- **Postmoore** → Security-Risiken, nur mit Drafts

**Nicht nutzen:**
- **Social Media Autopilot** → FB + TikTok fehlen

**Hinweis:** Bestehende Instagram + Facebook Pipeline läuft weiter. ClawHub nur für **TikTok-Erweiterung** und/oder Bulk-Scheduling.

---

### 🟢 OFFEN – NACH VPS

- 🟢 VPS einrichten (Ubuntu 24.04)
- 🟢 SearXNG installieren
- 🟢 OmniRoute installieren
- 🟢 `speech_router.py` (Nemotron ASR + Magpie TTS, Whisper-v3 als Alternative)
- 🟢 `video_router.py` (Cosmos3 Nano, Transfer2.5, Reasoner, Super-Res, Relighting)
- 🟢 Objekterkennung (`nemo-retriever-page-elements-v3`, PaddleOCR)
- 🟢 Remotion + Video-Pipeline autonom

---

### 🟣 STRATEGISCH

- 🟣 V8.6 Promotion Debug → main
- 🟣 Debug-Workflow-Split auflösen
- 🟣 OpenRouter 10 $ aufladen (nach Beobachtung)
- 🟣 Autonome Content-Fabrik (Vision)

---

### ⚠️ WICHTIGE HINWEISE

**NVIDIA API**
- Free-Tier: **25 Requests/Monat** pro Modell
- Rate-Limit: 40 RPM (theoretisch, aber Free-Tier limitiert)
- Endpoints:
  - Text: `https://integrate.api.nvidia.com/v1`
  - Bild: `https://ai.api.nvidia.com/v1/genai/<model>`
- Modell-Badges:
  - „Using free API for development" → ✅ nutzbar
  - „Downloadable" → ❌ meist kein Endpoint
  - „Upgrade" → ⚠️ kostenpflichtig

**API-Key**
- Aktiver Key: `KI-SOCIAL-AGENT-v2` (in GitHub Secrets als `NVIDIA_API_KEY`)
- Ablauf: **18.03.2027** → Reminder anlegen
- Nur in GitHub Secrets gespeichert, nirgendwo sonst

**Jules-Regeln**
- Max **3 parallele Sessions**
- Max **15 Credits/Tag**
- Reset: **~02:00 deutscher Zeit** (00:00 UTC)
- **Neuer Auftrag = neuer Chat**
- Fix an gemergtem PR = neuer Chat
- Credits verbrauchen pro Task-Run, nicht pro Prompt

**Branches**
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

**Telegram**
- ✅ Router-Fix erledigt → Telegram funktioniert normal

---

### 📊 CREDIT-STAND (Ende Tag 1)

- **Verbraucht heute:** ~14/15
- **Übrig:** ~1
- **Reset:** ~02:00 Uhr deutscher Zeit
- **Morgen verfügbar:** 15

**Heute verbraucht für:**
- Kimi K3 Config (1)
- image_router.py Versuch 1 (1, fehlgeschlagen – falscher Branch)
- image_router.py Versuch 2 (1)
- image_router.py Fix FLUX-Parameter (1)
- image_router.py Fix Timeout + klein-4b (1)
- Plus Reserve/Sonstiges

---

### 🎯 NÄCHSTE 3 TAGE

**Tag 2 (morgen, 20.09.)**
- 🚀 Test-Ergebnis auswerten (falls heute nicht fertig)
- 🚀 `vision_router.py` (Jules, 1 Credit)
- 🚀 `translation_router.py` (Jules, 1 Credit)
- 🎬 Erster Reel „10 Bikertreffs" bauen

**Tag 3 (21.09.)**
- 🧠 Memory-Embedding einbinden
- ⚙️ Router-Erweiterung (Config-Only)
- 📊 Erste Zahlen aus Instagram/Facebook

**Tag 4 (22.09.)**
- 🖥️ Approval-Dashboard Stufe 2 (Jules, 1 Credit)
- 📦 ClawHub-Skill Phy Social Post installieren (TikTok)

---

### 🚦 STAND DER AUTONOMIE

**Aktuell: ~40 %**

| Stufe | Status |
|---|---|
| 1. Planung (Weekly-Plan, Agents) | ✅ |
| 2. Recherche (Follow-Analyzer, Deal-Hunter) | ✅ |
| 3. Media-Generierung (Bild/Video/Audio) | 🔄 50 % (Bild in Arbeit, Video/Audio nach VPS) |
| 4. Compose (Caption + Hashtags) | ⏳ teilweise |
| 5. Approval (Telegram) | ✅ |
| 6. Publishing (Insta + FB) | ✅ |
| 7. Publishing (TikTok) | ❌ geplant |
| 8. Autonomie-Kette (durchgehend) | 🔴 fehlt |

**Ziel:** 100 % autonom = Agent macht alles, du gibst nur frei.

---

### 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **PRs:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **NVIDIA Build:** https://build.nvidia.com/models
- **ClawHub:** https://clawhub.ai
- **Handbuch:** `docs/HANDBUCH.md`
- **Übergabe:** `docs/PROJEKT_UEBERGABE.md`
### ✅ 19.09.2026 – Bild-Pipeline final

**image_router.py – Multi-Provider-Chain:**
- ✅ **Pollinations** = Primär (funktioniert, ~6 Sek, 374 KB, kein Key nötig)
- ✅ **Cloudflare** = Payload-Fix gemergt (nur `prompt` senden)
- ⚠️ **Together AI** = nicht verfügbar (Read-only Mode, Deposit nötig)
- ⏸️ **NVIDIA** = Timeout/422 (auf Eis)
- ✅ **Agnes** = letzte Instanz (funktioniert)

**Env-Schalter:** `IMAGE_PRIMARY` = `pollinations` (Standard im Test-Workflow)

**vision_router.py:**
- ✅ Gemergt
- Test-Workflow noch nicht angelegt

**Nächste Schritte:**
1. Test-Workflow für vision_router anlegen
2. translation_router.py starten
3. Erster Reel „10 Bikertreffs" bauen
