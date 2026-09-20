# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-19
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Autonome Content-Fabrik für Bülent (@edirnelibuelent) – 12–24 Monate zur KI-Agentur.

---

## 🏍️ BÜLENTS CONTENT-VISION (dauerhaft)

### Person & Nische
- Bülent, 50, fährt seit 1992 Motorrad
- Maschine: BMW M1000R, Baujahr 2024
- Region: Ruhrgebiet + Sauerland
- Hausstrecke: Radevormwald → Biggesee → Sägewerk
- Handle: **@edirnelibuelent**

### Ziel
Aus der Fabrik raus. Eigene KI-Agentur. Content, der autonom läuft.
Einnahmen: Sponsoren + Agentur-Kunden. Zeitachse: 12–24 Monate.

### Content-Säulen
1. **Strecken-Doku** – konkrete Strecken, Kurven, Bikertreffs (Ruhrgebiet)
2. **M1000R-Realität** – ehrliche Berichte (Kosten, Wartung, Erfahrung)
3. **Community** – gemeinsame Touren ab Radevormwald
4. **Biker-Alltag** – Generationen-Content, echte Geschichten

### Format
- Reels: 30–60 Sek, Hook in ersten 3 Sek, immer Untertitel
- Echte Fotos/Videos (kein KI-Editorial für Personenfotos)
- 1 Reel/Tag (Monat 1–6), 2–3/Tag (ab Monat 6)

### Schlachtplan
- **Woche 1:** Setup + 2 Reels
- **Monat 1:** 30 Reels, erste Zahlen
- **Monat 6:** 5.000 Follower, erste Kooperationen (100–500 €/Monat)
- **Monat 12:** 20.000 Follower, 2.500–3.500 €/Monat → Kündigung prüfen
- **Monat 24:** 50.000+ Follower, 10.000 €/Monat → Fabrik gekündigt

### Antrieb
Kinder. Für sie da sein. Ihnen ein besseres Leben ermöglichen.

---

## 🤖 ROUTER-STACK (Phase 1 – komplett)

Alle Router arbeiten autonom, mit Fallback-Ketten und Logging.

| Modul | Primär | Fallback | Status |
|---|---|---|---|
| `llm_router.py` | Groq/Google/OpenRouter/NVIDIA/Cloudflare | – | ✅ live |
| `image_router.py` | Pollinations | Cloudflare → Together → NVIDIA → Agnes | ✅ live |
| `vision_router.py` | Llama 3.2 Vision (NVIDIA) | Kimi K3 | ✅ live |
| `translation_router.py` | Riva 4B (NVIDIA) | llm_router | ✅ live |
| `speech_router.py` | Nemotron ASR + Magpie TTS | – | 🟢 nach VPS |
| `video_router.py` | Cosmos3 Nano | – | 🟢 nach VPS |

### Bild-Router Details
- **Env-Schalter:** `IMAGE_PRIMARY` = `pollinations` (Standard) | `cloudflare` | `together` | `nvidia` | `agnes`
- Cloudflare-Payload: nur `{"prompt": ...}` (NVIDIA-Check nötig)
- Together-Payload: OpenAI-kompatibel mit `model=black-forest-labs/FLUX.1-schnell-Free`
- Pollinations: OpenAI-kompatibel, funktioniert **ohne** Key zuverlässig
- NVIDIA FLUX: Timeout/422-Probleme, **auf Eis**
- Agnes: letzter Fallback, funktioniert zuverlässig

### Vision-Router Details
- `general` → `meta/llama-3.2-11b-vision-instruct` (Fallback: Kimi K3)
- `ocr` → `nvidia/nemotron-ocr-v2` (kein Fallback)
- `omni` → `nvidia/nemotron-3-nano-omni` (kein Fallback)

### Translation-Router Details
- Primär: `nvidia/riva-translate-4b-instruct-v2` (OpenAI-kompatibel)
- Fallback: `llm_router.quick_chat`
- **Wichtig:** Sprach-Namen ausgeschrieben („German", „Turkish") statt ISO-Codes
- Sprachen: DE, TR, EN, FR, ES, IT, NL, PL, RU, AR

---

## 🔑 API-KEYS & SECRETS

| Secret | Status | Wo |
|---|---|---|
| `NVIDIA_API_KEY` | `KI-SOCIAL-AGENT-v2` | GitHub Secrets |
| `CLOUDFLARE_ACCOUNT_ID` | aktiv | GitHub Secrets |
| `CLOUDFLARE_API_TOKEN` | aktiv | GitHub Secrets |
| `TOGETHER_API_KEY` | gesetzt, aber Account read-only | GitHub Secrets |
| `POLLINATIONS_API_KEY` | aktiv | GitHub Secrets |
| `GROQ_API_KEY` | aktiv | GitHub Secrets |
| `OPENROUTER_API_KEY` | aktiv | GitHub Secrets |
| `GEMINI_API_KEY` | aktiv | GitHub Secrets |
| `AGNES_API_KEY` | aktiv | GitHub Secrets |
| `PEXELS_API_KEY` | aktiv | GitHub Secrets |

### ⚠️ Provider-Status
- ✅ **Pollinations** – läuft, kein Key-Limit
- ✅ **Cloudflare Workers AI** – nach Payload-Fix nutzbar, 10k Neuronen/Tag
- ❌ **Together AI** – Read-only Mode, Deposit nötig → **nicht einplanen**
- ❌ **NVIDIA FLUX** – Timeout/422 → **auf Eis**
- ✅ **NVIDIA Riva 4B** (Translation) – läuft
- ✅ **NVIDIA Llama Vision** – läuft
- ✅ **Agnes** – Bild-Fallback
- ✅ **Kimi K3** – Reasoning/Coding
- ⚠️ **DeepSeek v4-flash** – EOL 22.09.2026, **nicht mehr nutzen**

---

## 🧪 TEST-WORKFLOWS (alle grün)

| Workflow | Zweck | Letztes Ergebnis |
|---|---|---|
| `test-image-router.yml` | Bild-Generierung testen | `BYTES: 386374` in 9 Sek |
| `test-vision-router.yml` | Vision-Analyse testen | `RESULT: {...}` |
| `test-translation-router.yml` | DE↔TR testen | `Merhaba, nasılsın?` / `Hallo, wie geht es dir?` |

---

## 🎬 CONTENT-PHASE (läuft)

**Aktuell:** Erster Reel „Bikertreff-Runde Teil 1"
- Konzept: Serie mit „Teil 2 folgt"-Hook
- 2–3 Spots pro Reel (nicht alle 10 auf einmal)
- Spots für Teil 1: Radevormwald + Biggesee
- Aufnahme: mit Handy, vertikal (9:16)
- Schnitt: CapCut (manuell, kostenlos)
- Format: 45–60 Sek, Hook in 3 Sek, immer Untertitel

**Nach Teil 1:** Teil 2 mit den nächsten 2–3 Bikertreffs aus `config/Bikertreffs.md`.

---

## 📦 CLAWHUB-SKILLS (geplant für Social-Media-Automatisierung)

**Empfohlen:**
- **Phy Social Post** → Insta + FB + TikTok + 5 weitere Plattformen
  - `openclaw skills install @phy041/phy-social-post`
- **Multi-Platform Scheduler** → Content-Kalender
- **Outfeed** → Bulk-Publishing (max. 25 Drafts)

**Mit Vorsicht:**
- **Postmoore** → Security-Risiken, nur mit Drafts

**Nicht nutzen:**
- **Social Media Autopilot** → FB + TikTok fehlen

**Hinweis:** Bestehende Instagram + Facebook Pipeline läuft weiter. ClawHub nur für **TikTok-Erweiterung** und/oder Bulk-Scheduling.

---

## 🖥️ APPROVAL-DASHBOARD (geplant)

**Aktuell:** Freigabe läuft über Telegram.

### Stufe 2 – KURZFRISTIG (1–2 Wochen)
- GitHub Pages, statische HTML-Seite
- Datenquelle: `docs/approval/queue.json`
- Vorschau: Bilder aus `assets/pending/`
- Freigabe: Button → `workflow_dispatch` → Publisher
- Auth: GitHub-Login
- Kosten: 0 €
- URL: `edirne22.github.io/KI-SOCIAL-AGENT/`

### Stufe 3 – NACH VPS (1–3 Monate)
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek, Multi-Account

---

## 🔴 OFFENE PRIORITÄTEN (nächste Tage)

### Kurzfristig (diese Woche)
- 🎬 Ersten Reel posten (in Arbeit)
- 🎬 Zweiten Reel planen (nächste 2–3 Bikertreffs)
- 🧠 Vision in Pipeline einbinden (Follow-Analyzer nutzt Llama Vision)
- 🖥️ Approval-Dashboard Stufe 2 (GitHub Pages)

### Mittelfristig (2 Wochen)
- 📦 TikTok-Integration (Apify + ClawHub)
- 🧠 Memory-Embedding → `nvidia/nemotron-3-embed-1b`
- 🛡️ Safety-Check → `nvidia/nemotron-3-content-safety`
- ⚙️ Router-Erweiterung (Nemotron Ultra/Super, GLM-5, Gemma)
- 🐛 Debug-Branch-Schutz (Branch-Protection)
- 📊 Analytics-Report für Instagram/Facebook

### Nach VPS
- 🟢 VPS einrichten (Ubuntu 24.04)
- 🟢 SearXNG installieren
- 🟢 OmniRoute installieren
- 🟢 `speech_router.py` (Nemotron ASR + Magpie TTS)
- 🟢 `video_router.py` (Cosmos3 Nano, Transfer, Reasoner)
- 🟢 Remotion + Video-Pipeline autonom

### Strategisch
- 🟣 V8.6 Promotion Debug → main
- 🟣 Debug-Workflow-Split auflösen
- 🟣 OpenRouter 10 $ aufladen (nach Beobachtung)
- 🟣 Autonome Content-Fabrik

---

## ⚠️ WICHTIGE REGELN

### Jules
- Free-Plan: **15 Sessions/Tag** (rollierend 24h), max 3 parallel
- **Neuer Auftrag = neuer Chat**
- Fix an gemergtem PR = neuer Chat
- Prompts präzise halten (spart Credits)

### Codex (ChatGPT Plus)
- Kann parallel zu Jules laufen
- **GitHub-verbundener Codex** kann PRs direkt anlegen
- **Lokaler Codex** braucht geklontes Repo (aktuell nicht vorhanden)
- Falls Nutzungslimit erreicht → auf Jules ausweichen

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

### Sicherheit
- **Kein Key in Chats posten** – immer nur in GitHub Secrets
- Bei versehentlichem Posten: sofort rotieren (alten löschen, neuen generieren)

### Telegram
- ✅ Router-Fix erledigt → Telegram funktioniert normal

---

## 📊 ZUSAMMENFASSUNG AUTONOMIE

| Stufe | Status |
|---|---|
| 1. Planung (Weekly-Plan, Agents) | ✅ |
| 2. Recherche (Follow-Analyzer, Deal-Hunter) | ✅ |
| 3. Media-Generierung (Bild/Vision/Translation) | ✅ Phase 1 |
| 4. Compose (Caption + Hashtags) | ⏳ teilweise |
| 5. Approval (Telegram) | ✅ |
| 6. Publishing (Insta + FB) | ✅ |
| 7. Publishing (TikTok) | ❌ geplant |
| 8. Media (Audio/Video) | 🟢 nach VPS |
| 9. Durchgehende Autonomie-Kette | 🔴 in Arbeit |

**Aktuell: ~50 % autonom.**

---

## 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **PRs:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **NVIDIA Build:** https://build.nvidia.com/models
- **ClawHub:** https://clawhub.ai
- **Handbuch:** `docs/HANDBUCH.md`
- **Bikertreffs:** `config/Bikertreffs.md`
- **Jules Docs:** https://jules.google/docs/usage-limits/

---

## 🎯 FÜR NEUE CHATS

**Startprompt für neuen Chat:**
> „Lies `docs/PROJEKT_UEBERGABE.md` im Repo Edirne22/KI-SOCIAL-AGENT (raw: https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/docs/PROJEKT_UEBERGABE.md). Arbeite auf diesem Stand weiter."

**Damit ist der Assistent in 10 Sekunden auf Stand.**
### 📱 WhatsApp-Communities (Bülents Zielgruppe direkt)

**Beigetreten:** 20.09.2026

#### 1. TÜRKBiR (Türkische Biker-Community)
- **Größe:** 36 Gruppen (bundesweit)
- **Relevante Gruppen:**
  - 🗺️ BERGISCHES LAND (regional)
  - 🏍️ TÜRKBiR-Buluşmalar (Treffen)
  - 🛣️ Tur ve buluşma bilgi (Touren)
  - 📅 Etkinlikler (Events)
  - 🤝 Welcome & Tanıtım (Vorstellung)

#### 2. BIKE SOCIETY (Deutsche Biker-Community – 3 Regionen)
- **United** → Ruhrgebiet + Ennepe-Ruhr-Kreis (13 Gruppen)
- **Hagen** → Hagen (12 Gruppen)
- **im Bergischen** → Bergisches Land (12 Gruppen)
- **Relevante Gruppen je Region:**
  - 📢 Ankündigungen (offizielle Infos)
  - 💬 Laberecke (Smalltalk)
  - 🏍️ Fahrten & Treffen (Touren)
  - 👋 Vorstellungsgruppe (neue Mitglieder)
  - 🗺️ Routen & Tourdaten (Strecken)

#### 🎯 Nutzen für Bülent
- **Direkter Zugang zur Zielgruppe** (Ruhrgebiet + Bergisches Land + türkische Szene)
- **Content-Ideen aus erster Hand** (was fahren die Leute? wo treffen sie sich?)
- **Community-Aufbau** für eigene Touren
- **Bikertreff-Recherche** – die Gruppen kennen alle Treffs
- **Kooperationen** mit Admins/Organisatoren

#### 🚦 Nächste Schritte
1. **2–3 Tage beobachten** (Ton, aktive Mitglieder, Themen)
2. **Vorstellen** in „Vorstellungsgruppe" (pro Community)
3. **Erste gemeinsame Tour** → Content für Reels
4. **Erst danach:** eigene Inhalte teilen (Reels, Touren-Ideen)

#### ⚠️ Regel
Nicht mit Werbung starten. Erst Community-Mitglied werden, dann Mehrwert liefern.
