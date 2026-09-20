# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-20
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Autonome Content-Fabrik für Bülent (@edirnelibuelent) – 12–24 Monate zur KI-Agentur.

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
1. **Strecken-Doku** – konkrete Strecken, Kurven, Bikertreffs (Ruhrgebiet/Bergisches)
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
- **Status:** Vorstellung in „Welcome & Tanıtım" erfolgt (Türkisch, ohne Werbung)
- **Relevante Gruppen:**
  - 🗺️ BERGISCHES LAND (regional)
  - 🏍️ TÜRKBiR-Buluşmalar (Treffen)
  - 🛣️ Tur ve buluşma bilgi (Touren)
  - 📅 Etkinlikler (Events)

### 2. BIKE SOCIETY (Deutsche Biker-Community – 3 Regionen)
- **Status:** Seit mehreren Monaten Mitglied
- **United** → Ruhrgebiet + Ennepe-Ruhr-Kreis (13 Gruppen)
- **Hagen** → Hagen (12 Gruppen)
- **im Bergischen** → Bergisches Land (12 Gruppen)
- **Relevante Gruppen je Region:**
  - 📢 Ankündigungen
  - 💬 Laberecke
  - 🏍️ Fahrten & Treffen
  - 👋 Vorstellungsgruppe
  - 🗺️ Routen & Tourdaten

### 🎯 Nutzen
- Direkter Zugang zur Zielgruppe (Ruhrgebiet + Bergisches Land + türkische Szene)
- Content-Ideen aus erster Hand
- Bikertreff-Recherche (Gruppen kennen alle Treffs)
- Community-Aufbau für eigene Touren
- Kooperationsmöglichkeiten mit Admins/Organisatoren

### 🚦 Nächste Schritte
1. TÜRKBiR: 2–3 Tage beobachten → erste Interaktion
2. BIKE SOCIETY: bereits etabliert → später eigene Inhalte teilen
3. Beide: Screenshots von „Fahrten & Treffen"-Posts → Content-Recherche

### ⚠️ Regel
Nicht mit Werbung starten. Erst Community-Mitglied werden, dann Mehrwert liefern.

---

## 🤖 ROUTER-STACK (Phase 1 – komplett)

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
- Cloudflare-Payload: nur `{"prompt": ...}`
- Together-Payload: OpenAI-kompatibel (`black-forest-labs/FLUX.1-schnell-Free`)
- Pollinations: OpenAI-kompatibel, funktioniert **ohne** Key zuverlässig
- NVIDIA FLUX: Timeout/422 → **auf Eis**
- Agnes: letzter Fallback, funktioniert zuverlässig

### Vision-Router Details
- `general` → `meta/llama-3.2-11b-vision-instruct` (Fallback: Kimi K3)
- `ocr` → `nvidia/nemotron-ocr-v2` (kein Fallback, liefert `text` + `tables`)
- `omni` → `nvidia/nemotron-3-nano-omni` (kein Fallback)

### Translation-Router Details
- Primär: `nvidia/riva-translate-4b-instruct-v2` (OpenAI-kompatibel)
- Fallback: `llm_router.quick_chat`
- **Wichtig:** Sprach-Namen ausgeschrieben („German", „Turkish") statt ISO-Codes
- Sprachen: DE, TR, EN, FR, ES, IT, NL, PL, RU, AR

---

## 🔑 API-KEYS & SECRETS

| Secret | Status |
|---|---|
| `NVIDIA_API_KEY` | `KI-SOCIAL-AGENT-v2` |
| `CLOUDFLARE_ACCOUNT_ID` | aktiv |
| `CLOUDFLARE_API_TOKEN` | aktiv |
| `TOGETHER_API_KEY` | gesetzt, aber Account read-only (nicht nutzbar) |
| `POLLINATIONS_API_KEY` | aktiv |
| `GROQ_API_KEY` | aktiv |
| `OPENROUTER_API_KEY` | aktiv |
| `GEMINI_API_KEY` | aktiv |
| `AGNES_API_KEY` | aktiv |
| `PEXELS_API_KEY` | aktiv |
| `TELEGRAM_BOT_TOKEN` | aktiv |
| `TELEGRAM_CHAT_ID` | aktiv |

### ⚠️ Provider-Status
- ✅ **Pollinations** – läuft, kein Key-Limit
- ✅ **Cloudflare Workers AI** – nach Payload-Fix, 10k Neuronen/Tag
- ❌ **Together AI** – Read-only Mode, Deposit nötig → **nicht einplanen**
- ❌ **NVIDIA FLUX** – Timeout/422 → **auf Eis**
- ✅ **NVIDIA Riva 4B** (Translation) – läuft
- ✅ **NVIDIA Llama Vision** – läuft
- ✅ **Agnes** – Bild-Fallback
- ✅ **Kimi K3** – Reasoning/Coding
- ⚠️ **DeepSeek v4-flash** – EOL 22.09.2026, **nicht mehr nutzen**

### 🔒 Sicherheitsregel
Keine Keys in Chats posten. Bei versehentlichem Posten: sofort rotieren (alten löschen, neuen generieren).

---

## 🧪 TEST-WORKFLOWS (alle grün)

| Workflow | Zweck | Letztes Ergebnis |
|---|---|---|
| `test-image-router.yml` | Bild-Generierung testen | `BYTES: 386374` in 9 Sek |
| `test-vision-router.yml` | Vision-Analyse testen | `RESULT: {...}` |
| `test-translation-router.yml` | DE↔TR testen | `Merhaba, nasılsın?` / `Hallo, wie geht es dir?` |

---

## 🤖 TELEGRAM VISION-BOT (Bild-Analyse)

**Status:** ✅ live seit 20.09.2026
**Datei:** `telegram_router.py`

### Funktionen
| Kommando | Wirkung |
|---|---|
| Bild + `/vision` | Bild analysieren (Standard) |
| Bild + `/ocr` | Text/Tabellen extrahieren |
| Bild + `/omni` | Multimodale Analyse |
| Bild ohne Caption | Standard = general |
| `/help` / `/hilfe` / `hilfe` | Kommando-Übersicht |
| `/vision` ohne Bild | Hinweis: „Bitte sende ein Bild" |

### Workflow
```
Screenshot von Instagram-Reel
    ↓
Telegram: Bild + Caption /vision
    ↓
Vision-Router (llama-3.2-11b-vision)
    ↓
Analyse kommt zurück in Telegram
    ↓
Bülent kopiert Analyse → KI-Chat → weitere Auswertung
```

### Einschränkungen
- Aktuell nur Bilder (keine Videos)
- Nach VPS: Video-Frames + Audio-Transkription

---

## 🎯 PATTERN LIBRARY (Instagram-Content-Bausteine)

**Datei:** `config/PATTERN_LIBRARY.md`
**Angelegt:** 20.09.2026

### Aktive Patterns
| # | Pattern | Quelle | Anwendung |
|---|---|---|---|
| 1 | Zahl + Nutzen im Hook | @aiwithshivang | Listen-Reels |
| 2 | Kommentar-Trigger | @aiwithshivang | Reichweite |
| 3 | Selfie mit VIP | Bülent (MotoGP) | Social Proof |
| 4 | Vorher/Nachher | vorgemerkt | Transformation |
| 5 | POV | vorgemerkt | Fahrt-Content |
| 6 | Storytelling mit Ende offen | vorgemerkt | Serie |

### Workflow
```
Instagram-Post gefällt
    ↓
Screenshot → Telegram-Bot (/vision)
    ↓
Analyse → Bülent prüft: neues Pattern?
    ↓
Wenn ja: in PATTERN_LIBRARY.md eintragen
    ↓
Bei Reel-Planung: Generate-Ideas-Agent nutzt Patterns
```

### Ziel
15–20 Patterns bis Ende Oktober 2026.

---

## 🎬 CONTENT-MATERIAL (Bülent, Stand 20.09.2026)

### 4 Foto-/Video-Ordner auf Laptop

| Ordner | Inhalt | Reel-Potenzial |
|---|---|---|
| **MotoGP Assen 2026** | Toprak (Video + Selfies), Jack Miller, Morbidelli, Rins, Ai Ogura, Strecke, Stände | 🔥 **höchstes** |
| **Radevormwald** | Fotos | mittel |
| **BiggeGrill / Biggesee** | Fotos | mittel |
| **Hagen Biker Treff** | Fotos | mittel |
| **M1000R Übungsplatz** | Kreise fahren, Achten, Hinterreifen, Helm, Straße von oben | hoch |

### Bonus-Material
- BMW-App-Screenshot: Route + Schräglagen (47° rechts / 44° links)
- Calimoto (falls aufgezeichnet)

### 🏆 Top-Material: MotoGP Assen 2026
- 🎥 **Toprak-Video:** bedankt sich auf Türkisch, winkt in Kamera
- 📸 Selfies mit Toprak, Jack Miller, Morbidelli, Rins
- 📸 Ai Ogura (von weitem)
- 📸 Strecke + Stände

**Virales Potenzial:** 3 Zielgruppen gleichzeitig (Türken, MotoGP-Fans, Biker)

### 🎯 Reel-Plan (priorisiert)
| # | Reel | Status |
|---|---|---|
| 1 | MotoGP Assen – „Toprak bedankt sich" | 🔴 Storyboard fertig |
| 2 | Bikertreff-Runde (Radevormwald + Biggesee) | 🔴 Storyboard fertig |
| 3 | Hagen Biker Treff | ⏸️ wartet |
| 4 | M1000R-Realität (Reifen, Helm, Übungsplatz) | ⏸️ wartet |
| 5 | BiggeGrill | ⏸️ wartet |

### 🛠️ Video-Tool-Entscheidung
- **CapCut:** ❌ zu groß für Laptop
- **HeyGen:** ✅ kostenloser Plan (3 Videos/Monat, 1 Min, 720p, Wasserzeichen)
- **OpenReel:** ✅ Browser-Alternative (kein Install, kein Wasserzeichen)
- **Empfehlung:**
  - MotoGP-Reel: manuell (OpenReel) – emotionale Story
  - Andere Reels: HeyGen für Rohschnitt

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

### Stufe 3 – NACH VPS
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek, Multi-Account

---

## 📦 CLAWHUB-SKILLS (Social-Media-Automatisierung)

**Empfohlen:**
- **Phy Social Post** → Insta + FB + TikTok (Install: `openclaw skills install @phy041/phy-social-post`)
- **Multi-Platform Scheduler** → Content-Kalender
- **Outfeed** → Bulk-Publishing (max. 25 Drafts)

**Mit Vorsicht:**
- **Postmoore** → Security-Risiken, nur mit Drafts

**Hinweis:** Bestehende Instagram + Facebook Pipeline läuft weiter. ClawHub nur für **TikTok-Erweiterung** und/oder Bulk-Scheduling.

---

## 🔴 OFFENE PRIORITÄTEN

### Kurzfristig (diese Woche)
- 🎬 MotoGP-Reel bauen + posten (Pattern 1 anwenden)
- 🎬 Bikertreff-Reel (Radevormwald + Biggesee)
- 📸 Instagram durchforsten → Patterns sammeln
- 📱 TÜRKBiR beobachten → erste Interaktion in 2–3 Tagen
- 📄 `config/MEDIA_TOOLS.md` anlegen (nur manuelle Tools: CapCut, OpenReel, Canva, DaVinci, HeyGen)

### Mittelfristig (2 Wochen)
- 🖥️ Approval-Dashboard Stufe 2 (GitHub Pages)
- 📦 TikTok-Integration (Apify + ClawHub)
- 🧠 Vision in Pipeline einbinden (Follow-Analyzer nutzt Llama Vision)
- 🧠 Memory-Embedding → `nvidia/nemotron-3-embed-1b`
- 🛡️ Safety-Check → `nvidia/nemotron-3-content-safety`
- ⚙️ Router-Erweiterung (Nemotron Ultra/Super, GLM-5, Gemma)
- 🐛 Debug-Branch-Schutz (Branch-Protection)
- 📊 Analytics-Report Instagram/Facebook

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

## 🔧 TOOL-WORKFLOW (Jules + Codex)

### Jules (Google)
- **Kontingent:** 15 Sessions/Tag (rollierend 24h), max 3 parallel
- **Stärke:** Automatische PRs, GitHub-Integration
- **Regel:** Neuer Auftrag = neuer Chat
- **Fix an gemergtem PR = neuer Chat**

### Codex (ChatGPT Plus)
- **Kontingent:** Nutzungslimit, Reset ~18:41 Uhr
- **Stärke:** Kann GitHub-PRs direkt anlegen (GitHub-Verbindung)
- **Regel:** Selbst-enthaltende Aufträge (kein Chat-Gedächtnis)

### Aufteilung
- **Jules:** Größere Tasks, mehrstufige Aufträge
- **Codex:** Fixes, kleine PRs, parallel zu Jules
- **Beide:** Nie dieselbe Datei gleichzeitig bearbeiten

---

## ⚠️ WICHTIGE REGELN

### Verbotene Clubs (nie erwähnen, nie taggen)
- ❌ Osmanen Germania (verboten 2018)
- ❌ Turkos MC (aufgelöst 2018)
- ❌ Black Jackets (kriminell)

### Content-Regeln
- ✅ Immer Türkisch + Deutsch (Zielgruppe)
- ✅ Nur öffentliche Infos verwenden
- ✅ Respektvoll & positiv
- ✅ Keine politischen Aussagen
- ✅ Handles nur, wenn öffentlich sichtbar
- ❌ Keine KI-Deepfakes von echten Personen
- ❌ Kein Re-Upload ohne Freigabe

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

### Telegram
- ✅ Router-Fix erledigt → funktioniert normal

---

## 📊 AUTONOMIE-STAND

| Stufe | Status |
|---|---|
| 1. Planung (Weekly-Plan, Agents) | ✅ |
| 2. Recherche (Follow-Analyzer, Deal-Hunter) | ✅ |
| 3. Media (Bild/Vision/Translation) | ✅ Phase 1 |
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
- **Pattern Library:** `config/PATTERN_LIBRARY.md`
- **Jules Docs:** https://jules.google/docs/usage-limits/

---

## 🎯 FÜR NEUE CHATS

**Startprompt für neuen Chat:**
> „Lies `docs/PROJEKT_UEBERGABE.md` im Repo Edirne22/KI-SOCIAL-AGENT (raw: https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/docs/PROJEKT_UEBERGABE.md). Arbeite auf diesem Stand weiter."

**Damit ist der Assistent in 10 Sekunden auf Stand.**