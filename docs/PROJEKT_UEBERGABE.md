# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-22 (Mittag)
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Autonome Content-Fabrik für Bülent (@edirnelibuelent) – 12–24 Monate zur KI-Agentur.
**Repo-Typ:** 🌐 Public (unbegrenzte GitHub-Actions-Minuten)
**Telegram-Polling:** alle 2 Min zwischen 06:00–21:00 Uhr

---

## 🏍️ BÜLENTS CONTENT-VISION (dauerhaft)

### Person & Nische
- Bülent, 50, fährt seit 1992 Motorrad
- Maschine: BMW M1000R, Baujahr 2024
- Region: Schwelm (Ruhrgebiet + Sauerland + Bergisches Land)
- Hausstrecke: Radevormwald → Biggesee → Sägewerk
- Handle: **@edirnelibuelent**

### Ziel
Aus der Fabrik raus. Eigene KI-Agentur. Content, der autonom läuft.
Einnahmen: Sponsoren + Agentur-Kunden. Zeitachse: 12–24 Monate.

### Content-Säulen
1. **Strecken-Doku** – konkrete Strecken, Kurven, Bikertreffs
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

## 📱 WHATSAPP-COMMUNITIES (direkter Zielgruppen-Zugang)

### 1. TÜRKBiR (Türkische Biker-Community)
- **Beigetreten:** 20.09.2026
- **Größe:** 36 Gruppen (bundesweit)
- **Status:** Vorstellung in „Welcome & Tanıtım" erfolgt
- **Relevante Gruppen:** BERGISCHES LAND, Buluşmalar, Tur ve buluşma bilgi, Etkinlikler

### 2. BIKE SOCIETY (Deutsche Biker-Community – 3 Regionen)
- **Status:** Seit mehreren Monaten Mitglied
- **United** → Ruhrgebiet + Ennepe-Ruhr-Kreis (13 Gruppen)
- **Hagen** → Hagen (12 Gruppen)
- **im Bergischen** → Bergisches Land (12 Gruppen)
- **Relevante Gruppen:** Ankündigungen, Laberecke, Fahrten & Treffen, Vorstellungsgruppe, Routen & Tourdaten

### 🎯 Nutzen
- Direkter Zugang zur Zielgruppe
- Content-Ideen aus erster Hand
- Bikertreff-Recherche
- Kooperationen

### 🚦 Nächste Schritte
1. TÜRKBiR: 2–3 Tage beobachten → erste Interaktion
2. BIKE SOCIETY: eigene Inhalte später teilen
3. Screenshots von „Fahrten & Treffen"-Posts → Content-Recherche

### ⚠️ Regel
Nicht mit Werbung starten. Erst Community-Mitglied werden, dann Mehrwert liefern.

---

## 🤖 ROUTER-STACK (Phase 1 – komplett)

| Modul | Primär | Fallback | Status |
|---|---|---|---|
| `llm_router.py` | Groq/Google/OpenRouter/NVIDIA/Cloudflare | – | ✅ live |
| `image_router.py` | Pollinations | Cloudflare → Together → NVIDIA → Agnes | ✅ live |
| `vision_router.py` | Muse Glimmer 30B (NVIDIA) | Kimi K3 | ✅ live |
| `translation_router.py` | Riva 4B (NVIDIA) | llm_router | ✅ live |
| `speech_router.py` | Nemotron ASR + Magpie TTS | – | 🟢 nach VPS |
| `video_router.py` | Cosmos3 Nano | – | 🟢 nach VPS |

### Bild-Router Details
- **Env-Schalter:** `IMAGE_PRIMARY` = `pollinations` (Standard) | `cloudflare` | `together` | `nvidia` | `agnes`
- Cloudflare-Payload: nur `{"prompt": ...}`
- Together: Read-only Mode, nicht nutzbar
- Pollinations: läuft ohne Key zuverlässig
- NVIDIA FLUX: **auf Eis** (Timeout/422)
- Agnes: letzter Fallback, funktioniert

### Vision-Router Details
- `general` → `meta/muse-glimmer-30b` (Fallback: Kimi K3)
  - Timeout 240 Sekunden
  - Deutscher, strukturierter Prompt
- `ocr` → `nvidia/nemotron-ocr-v2` (liefert `text` + `tables`, Timeout 180s)
- `omni` → `nvidia/nemotron-3-nano-omni` (Timeout 180s)

### Translation-Router Details
- Primär: `nvidia/riva-translate-4b-instruct-v2`
- Fallback: `llm_router.quick_chat`
- **Wichtig:** Sprach-Namen ausgeschrieben („German", „Turkish")
- Sprachen: DE, TR, EN, FR, ES, IT, NL, PL, RU, AR

---

## 🔑 API-KEYS & SECRETS

| Secret | Status |
|---|---|
| `NVIDIA_API_KEY` | `KI-SOCIAL-AGENT-v2` |
| `CLOUDFLARE_ACCOUNT_ID` | aktiv |
| `CLOUDFLARE_API_TOKEN` | aktiv |
| `TOGETHER_API_KEY` | gesetzt, aber nicht nutzbar |
| `POLLINATIONS_API_KEY` | aktiv |
| `GROQ_API_KEY` | aktiv |
| `OPENROUTER_API_KEY` | aktiv |
| `GEMINI_API_KEY` | aktiv |
| `AGNES_API_KEY` | aktiv |
| `PEXELS_API_KEY` | aktiv |
| `TELEGRAM_BOT_TOKEN` | aktiv |
| `TELEGRAM_CHAT_ID` | aktiv |
| `OPENWEATHER_API_KEY` | aktiv |

### Provider-Status
- ✅ **Pollinations** – läuft
- ✅ **Cloudflare Workers AI** – 10k Neuronen/Tag
- ❌ **Together AI** – nicht nutzbar
- ❌ **NVIDIA FLUX** – auf Eis
- ✅ **NVIDIA Riva 4B** – läuft
- ✅ **NVIDIA Muse Glimmer 30B** – läuft
- ✅ **Agnes** – Bild-Fallback
- ✅ **Kimi K3** – Reasoning/Coding + Vision-Fallback
- ⚠️ **DeepSeek v4-flash** – EOL 22.09.2026
- ⚠️ **GLM-4.7** – EOL 14.05.2026
- ⚠️ **Qwen3 Coder 480B** – EOL 11.06.2026
- ✅ **Nemotron 3.5 Lightning 30B** – aktiv für Claude Code (via OmniRoute)

### 🔒 Sicherheitsregel
Keine Keys in Chats posten. Bei versehentlichem Posten: sofort rotieren.

---

## 🧪 TEST-WORKFLOWS (alle grün)

| Workflow | Zweck | Letztes Ergebnis |
|---|---|---|
| `test-image-router.yml` | Bild-Generierung | `BYTES: 386374` in 9 Sek |
| `test-vision-router.yml` | Vision-Analyse | `RESULT: {...}` |
| `test-translation-router.yml` | DE↔TR | `Merhaba, nasılsın?` |

---

## 🤖 TELEGRAM VISION-BOT (Bild-Analyse)

**Status:** ✅ live seit 20.09.2026
**Dateien:** `telegram_router.py`, `memory/VISION_LOG.jsonl`, `memory/VISION_SUMMARY.md`

### Funktionen
| Kommando | Wirkung |
|---|---|
| Bild + `/vision` | Bild analysieren |
| Bild + `/ocr` | Text/Tabellen extrahieren |
| Bild + `/omni` | Multimodale Analyse |
| Bild ohne Caption | Standard = general |
| `/help` / `/hilfe` | Kommando-Übersicht |
| `/vision` ohne Bild | Hinweis |

### Vision-Log-Speicherung (live)
- Jede Analyse wird in `memory/VISION_LOG.jsonl` geschrieben

### Vision-Summary-Agent (live)
- **Datei:** `agents/vision_summary_agent.py`
- **Workflow:** `.github/workflows/vision-summary.yml`
- **Lauf:** alle 3 Tage um 08:00 UTC
- **Erster regulärer Lauf:** 18.10.2026 (Guard-Clause)
- **Force-Modus:** `workflow_dispatch` mit `force=true`
- **Output:** `memory/VISION_SUMMARY.md`

---

## 🌤️ WEATHER AGENT

**Status:** ✅ live + getestet (21.09.2026)
**Dateien:** `config/strecken.json`, `agents/weather_agent.py`, `.github/workflows/weather_agent.yml`

### Was er macht
- Liest Hausstrecken aus `config/strecken.json`
- **Nutzt Forecast-API** (nicht mehr Current-Weather)
- Zeigt Vorhersage für **09:00 UTC = 11:00 deutsche Zeit**
- Filtert: Regen/Schnee/Sturm → „nicht empfohlen"
- Sendet Telegram-Nachricht
- Cron: täglich 06:00 UTC

### Testausgabe (21.09.2026)