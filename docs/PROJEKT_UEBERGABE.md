# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-26
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Autonome Content-Fabrik für Bülent (@edirnelibuelent) – 12–24 Monate zur KI-Agentur.
**Repo-Typ:** 🌐 Public (unbegrenzte GitHub-Actions-Minuten)
**Telegram-Polling:** alle 2 Min zwischen 06:00–21:00 Uhr

---

## 🔧 ÜBERGABE-DETAIL-DATEIEN

| # | Datei | Inhalt |
|---|---|---|
| 1 | `PROJEKT_UEBERGABE.md` | Hauptübergabe (immer aktuell) |
| 2 | `PROJEKT_UEBERGABE_2_ENGAGEMENT.md` | Agent 17 + 18, Meta Webhook, Reply Adapter |
| 3 | `PROJEKT_UEBERGABE_3_RACING.md` | Racing-Pipeline-Hardening 26.09.2026 |

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

### Racing-LLM-Router (MotoGP-Pipeline)
- Nutzt **eigenen Pfad** über `llm_client.py` + `config/model_router.json`
- **Nicht** über `llm_router.py`
- **Fallback-Kette (24.09.):** Agnes → Gemini → NVIDIA → fail-closed
- **429-Cooldown:** Retry-After-Header oder 60 Sek
- **NVIDIA-Modell:** `nvidia/nemotron-3.5-lightning-30b-a3b` (alt: `minimaxai/minimax-m3` – abgekündigt, HTTP 410)

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
| `INSTAGRAM_USER_ID` | aktiv |
| `INSTAGRAM_ACCESS_TOKEN` | aktiv |
| `FACEBOOK_PAGE_ID` | aktiv |
| `FACEBOOK_PAGE_TOKEN` | ⚠️ Problem (pages_read_engagement fehlt) |
| `META_WEBHOOK_VERIFY_TOKEN` | geplant (nach VPS) |
| `META_APP_SECRET` | geplant (nach VPS) |

### Provider-Status
- ✅ **Pollinations** – läuft
- ✅ **Cloudflare Workers AI** – 10k Neuronen/Tag
- ❌ **Together AI** – nicht nutzbar
- ❌ **NVIDIA FLUX** – auf Eis
- ✅ **NVIDIA Riva 4B** – läuft
- ✅ **NVIDIA Muse Glimmer 30B** – läuft
- ✅ **Agnes** – Bild + Text (Free-Tier mit Rate-Limit)
- ✅ **Kimi K3** – Reasoning/Coding + Vision-Fallback
- ⚠️ **DeepSeek v4-flash** – EOL 22.09.2026
- ⚠️ **GLM-4.7** – EOL 14.05.2026
- ⚠️ **Qwen3 Coder 480B** – EOL 11.06.2026
- ✅ **Nemotron 3.5 Lightning 30B** – aktiv für Claude Code (via OmniRoute) + Racing-Fallback

### 🔒 Sicherheitsregel
Keine Keys in Chats posten. Bei versehentlichem Posten: sofort rotieren.

---

## 🧪 TEST-WORKFLOWS

| Workflow | Zweck | Status |
|---|---|---|
| `test-image-router.yml` | Bild-Generierung | ✅ grün |
| `test-vision-router.yml` | Vision-Analyse | ✅ grün |
| `test-translation-router.yml` | DE↔TR | ✅ grün |
| `instagram-api-test.yml` | Instagram Endpoint-Check | ✅ grün |
| `instagram-reply-adapter-test.yml` | Reply Adapter Mock | ✅ SUCCESS |
| `instagram-og-image-test.yml` | og:image Format-Test | ✅ grün |
| `instagram-false-success-hotfix-test.yml` | False-Success-Prüfung | ✅ grün |
| `racing-manual-selection-test.yml` | Manual Racing Selection | ✅ grün |
| `racing-series-lock-regression.yml` | Series-Lock Preflight | ✅ grün |

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

### Vision-Log-Speicherung (live)
- Jede Analyse wird in `memory/VISION_LOG.jsonl` geschrieben

### Vision-Summary-Agent (live)
- **Datei:** `agents/vision_summary_agent.py`
- **Workflow:** `.github/workflows/vision-summary.yml`
- **Lauf:** alle 3 Tage um 08:00 UTC
- **Erster regulärer Lauf:** 18.10.2026 (Guard-Clause)
- **Output:** `memory/VISION_SUMMARY.md`

---

## 🌤️ WEATHER AGENT

**Status:** ✅ live + getestet (21.09.2026)
**Dateien:** `config/strecken.json`, `agents/weather_agent.py`

### Was er macht
- Liest Hausstrecken aus `config/strecken.json`
- Nutzt **Forecast-API** (nicht mehr Current-Weather)
- Zeigt Vorhersage für **09:00 UTC = 11:00 deutsche Zeit**
- Filtert: Regen/Schnee/Sturm → „nicht empfohlen"
- Sendet Telegram-Nachricht
- Cron: täglich 06:00 UTC

---

## 🎯 PATTERN LIBRARY (Instagram-Content-Bausteine)

**Datei:** `config/PATTERN_LIBRARY.md`
**Stand:** 23.09.2026 – **17 Patterns aktiv**
**Ziel:** 20 Patterns bis Ende Oktober 2026

| # | Pattern | Quelle |
|---|---|---|
| 1 | Zahl + Nutzen im Hook | @aiwithshivang |
| 2 | Kommentar-Trigger | @aiwithshivang |
| 3 | Selfie mit VIP | Bülent (MotoGP) |
| 4 | Vorher/Nachher | vorgemerkt |
| 5 | POV | vorgemerkt |
| 6 | Storytelling | vorgemerkt |
| 7 | Karussell als Cheat-Sheet | @karishmaticmarketer |
| 8 | Slash-Command-Tags | @karishmaticmarketer |
| 9 | Fotografie-Stil-Prompts | @mauryavanshi_edits |
| 10 | Skill-Karten-Raster | @bitbyybit |
| 11 | Tool-Stack-Karussell | @rakeshmahantiai |
| 12 | Paid vs Free (kompakt) | @aitoolswithpritham |
| 13 | Step-by-Step Tutorial | @aiagently |
| 14 | X Free Tools-Liste | @infinity_digitals_official |
| 15 | Pre-Purchase-Check | Türkisch |
| 16 | Tool-Steckbrief als Karussell | @aiwithshivang |
| 17 | Paid vs Free (Detail) | @aitoolswithpratham u.a. |

**Referenz-Accounts:**
@startup_rules, @mauryavanshi_edits, @karishmaticmarketer,
@bitbyybit, @rakeshmahantiai, @aitoolswithpritham,
@aiagently, @alpedya, @aiwithshivang,
@trickplus.ai, @chatgptricks, @codescaptain,
@its_aaditya, @haroonaicreator, @infinity_digitals_official,
@hfnhq

**Bonus:** Tool-Alternativen-Sektion + KI-Rollen-Bibliothek (15 Rollen)

---

## 📺 MOTOGP CONTENT PIPELINE (V8.5.5)

### Workflows
| Workflow | Trigger | Zweck |
|---|---|---|
| `motogp-content-agency.yml` | schedule + workflow_dispatch | 5 Tagesvorschläge generieren |
| `motogp-telegram-approval.yml` | nur workflow_dispatch | Empfängt MotoGP-Kommandos |
| `telegram-receive.yml` | schedule alle 2 Min | Zentraler Router |
| `motogp-pipeline-diagnose.yml` | workflow_dispatch | Diagnose |
| `motogp-roster-update.yml` | schedule | Fahrer-Roster aktualisieren |

### Telegram-Befehle
- `motogp 1–5` – einzelne Auswahlen freigeben
- `motogp alle` – alle freigeben
- `motogp nein` – alle ablehnen
- `racing top10` – Top 10 anzeigen (manuelle Auswahl)
- `racing top20` – Top 20 anzeigen
- `racing artikel <Nr>` – Artikel einzeln auswählen

### Instagram Zwei-Stufen-Freigabe
- **Facebook:** postet sofort nach Telegram-Freigabe
- **Instagram:** wartet auf zweite Freigabe
  1. Freigabe → Bild generiert (og:image oder Agnes-Fallback)
  2. Bild kommt in Telegram
  3. `bild ✅` → posten
  4. `bild ❌` → neu generieren

### Wichtige Erkenntnisse
- **5 → 3 Stories möglich** wenn FRESHNESS DIAG filtert
- **FRESHNESS DIAG** filtert nach: fresh / old / missing_date / promo_irrelevant
- **SERIES LOCK:** immutable series + source-fact whitelist
- **6 Struktur-Varianten:** HOOK_BODY_QUESTION, BODY_QUESTION, STORY_QUESTION, FACT_FACT_FACT, QUESTION_HOOK_BODY, ZITAT_BODY
- **QM erkennt alle 6 Varianten**
- **Community-Fallback:** siehe `PROJEKT_UEBERGABE_3_RACING.md`

### `force_new_run` (Workflow-Input)
- GitHub-Checkbox „V8.5: duplicate protection bewusst umgehen"
- Bei gesetztem Haken: Doppelte Ausführung im selben Zeitfenster erlaubt
- Log-Zeile: `force_new_run resolved=true`

---

## ⚡ FFMPEG-WERKZEUGE (Standard für Video!)

### Kernlehre 22.09.2026
**FFmpeg direkt schlägt MCP-Tools bei einfachen Video-Aufgaben um Längen.**

Der Umweg über Kinocut/claudeclip + OmniRoute + NVIDIA Nemotron kostete **Stunden** (504er, Streaming-Abbrüche, Rate-Limits). Ein FFmpeg-Skript baute den kompletten MotoGP-Reel in **~3 Minuten**.

### Wann FFmpeg, wann MCP?

| Aufgabe | Werkzeug |
|---|---|
| Einmal-Video mit fixem Plan | **FFmpeg** |
| Text-Overlays, Concat, Musik | **FFmpeg** |
| Wiederkehrende Reels, gleiche Struktur | FFmpeg-Skript mit Variablen |
| Interaktive Anpassungen, viele Varianten | MCP (Kinocut/claudeclip) |
| Video-Generierung aus Text | KI-Tool (Sora, Runway) – NICHT für Personenfotos |

### Fertige Skripte
- **Reel-Build:** `D:\reel-build.ps1`
- **Musik-Befehl:** FFmpeg-Einzeiler mit `amix`
- **Einzel-Clip-Nachbau:** Text-Datei neu + Concat wiederholen

### Wichtige Details
- **Emojis funktionieren NICHT** mit Standard-Font
- **Text-Dateien UTF-8 ohne BOM**
- **Umlaute in Dateinamen** vermeiden
- **Font-Pfad:** `C\:/Windows/Fonts/arialbd.ttf`
- **`amix` mit `duration=first`** → Musik nimmt Videolänge

---

## 🎬 VIDEO-PRODUKTIONS-SYSTEM (MCP – nur wenn nötig)

**Komplette Kette:**
```
Claude Code → OmniRoute (Port 20128) → NVIDIA NIM (Nemotron 3.5 Lightning)
→ MCP: kinocut (~150 Tools) ODER claudeclip (31 Tools) → FFmpeg → Videos
```

### Installationen auf Bülents Laptop

| Was | Version | Pfad |
|---|---|---|
| Node.js | v24.21.0 | C:\Program Files\nodejs\ |
| npm | 11.19.0 | prefix: D:\npm-global |
| OmniRoute | v3.8.50 | D:\npm-global\omniroute.cmd |
| Claude Code | v2.1.278 | C:\Users\Admin\AppData\Roaming\npm\claude.cmd |
| FFmpeg | 9.0.2-essentials | E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin |
| Python | 3.14.7 | C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\ |
| claudeclip | aktuell | D:\npm-global\node_modules\claudeclip\ |
| kinocut | 1.15.1 | Python 3.14 – ~150 Tools |
| Kaestral | 1.0.5 | MCP-Server – Fallback |

### Claude Code Startsequenz

**Fenster 1 – OmniRoute:**
```powershell
$env:OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS="120000"
$env:OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS="120000"
D:\npm-global\omniroute.cmd
```

**Fenster 2 – Claude Code:**
```powershell
$env:PATH = $env:PATH + ";C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts"
cd C:\Users\Admin
$env:ANTHROPIC_BASE_URL="http://localhost:20128"
$env:ANTHROPIC_API_KEY="dein-omni-key"
$env:TMP="D:\ffmpeg-temp"
$env:TEMP="D:\ffmpeg-temp"
C:\Users\Admin\AppData\Roaming\npm\claude.cmd --model "nvidia/nvidia/nemotron-3.5-lightning-30b-a3b"
```

**Auto-Mode:** Shift+Tab bis `⏵⏵ auto mode on`

### Video-MCPs (nur EINER gleichzeitig!)
- **kinocut** (1.15.1, ~150 Tools) – guardrailed FFmpeg-Wrapper
- **claudeclip** (31 Tools) – Standard-Fallback
- **Kaestral** (52 Tools) – ⚠️ verwirrt Nemotron

### MotoGP-Material-Pfad
`D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\`

---

## 🎬 CONTENT-MATERIAL (Übersicht)

| Ordner | Inhalt | Potenzial |
|---|---|---|
| MotoGP Assen 2026 | Toprak, Jack Miller, Morbidelli, Rins, Ai Ogura, Strecke, Stände | 🔥 höchstes |
| Radevormwald | Fotos | mittel |
| BiggeGrill / Biggesee | Fotos | mittel |
| Hagen Biker Treff | Fotos | mittel |
| M1000R Übungsplatz | Kreise, Achten, Reifen, Helm | hoch |

### Top-Material: MotoGP Assen 2026
- 🎥 Toprak-Video (Dank auf Türkisch)
- 🎥 Autogramm-Video
- 🎥 Moderator-Video
- 📸 Gruppenselfie mit Moderator + Helfer + Damian
- 📸 Selfies mit Toprak, Jack Miller, Morbidelli, Rins

---

## 🎯 MOTOGP-REEL – FERTIG ✅

**Status:** ✅ Fertig + auf Instagram + Facebook gepostet (22.09.2026)
**Datei:** `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\build\reel-final-mit-musik.mp4`
**Länge:** 65 Sek · 1080x1920 · 30fps · 21 MB

### Szenen (final)

| # | Datei | Dauer | Text |
|---|---|---|---|
| 1 | gruppenselfieModerator.jpg | 4s | „Er fragte: Wollt ihr zu Toprak?" |
| 2 | autogrammToprak.mp4 | 24s | „Der Moderator hat's möglich gemacht" |
| 3 | toprak-selfie.jpg | 5s | „Toprak Razgatlioglu" |
| 4 | toprak-dankesagen.mp4 | 7s | „Danke Toprak" (Original-Ton!) |
| 5 | ich-herowalk.jpg | 5s | „Hero Walk – hautnah" |
| 6 | strecke.jpg | 5s | „Assen 2026 – die Strecke" |
| 7 | MotoGP-ständer.jpg | 4s | „Die MotoGP-APP" |
| 8 | toprak-selfie.jpg | 5s | „Teil 2 folgt – wer ist euer Favorit?" |

### Reel-Plan (nächste)

| # | Reel | Status |
|---|---|---|
| 1 | MotoGP Assen | ✅ fertig + gepostet |
| 2 | Bikertreff-Runde (Radevormwald + Biggesee) | 🔴 Storyboard fertig |
| 3 | Hagen Biker Treff | ⏸️ wartet |
| 4 | M1000R-Realität | ⏸️ wartet |
| 5 | BiggeGrill | ⏸️ wartet |

---

## 🧠 EXPERT AGENT (Konzept)

**Was es ist:** Ein Claude-Code-Skill, der aus 10 YouTube-Tutorials trainiert wird.

**Was es NICHT ist:**
- Kein kontinuierlich lernender Agent
- Kein autonom suchender Agent
- Kein Feedback-Loop ohne Nutzer

**Geplantes Langzeitgedächtnis:**
- `CLAUDE.md` im Repo-Root
- `memory/EXPERT_SKILLS/` Ordner
- `memory/EXPERT_EVENTS.jsonl`
- Basic Memory MCP

**Erste Kandidaten:** MotoGP-Reel-Schnitt, Bikertreff-Video-Stil, Hook-Writer

---

## 🖥️ APPROVAL-DASHBOARD

**Stufe 2 – ✅ UMGESETZT (22.09.2026)**
- `docs/approval/index.html` – Freigabe-Liste
- `docs/approval/app.js` – Vanilla JS + localStorage
- `.github/workflows/pages.yml` – Deploy
- URL: `edirne22.github.io/KI-SOCIAL-AGENT/`
- **TODO Stufe 3 im Code:** Entscheidung an Pipeline senden

### Stufe 3 – NACH VPS
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek

---

## 🎨 HUMAN WRITING PROTOCOL

**Datei:** `config/HUMAN_WRITING_PROTOCOL.md` (V1.0)

**Zweck:** Verbindliche Regeln gegen KI-Sprech in allen Texten.
**Aktiv eingebunden in:** `llm_client.py` (globaler Kontext für alle Text-Prompts).

**Kernprinzip:** Natürlichkeit über Perfektion.

**Verwandte Dateien:**
- `config/PROFESSIONAL_AGENT_STANDARD.md`
- `memory/MOTOGP_VOICE_RULES.md` (Bülent-Stil)
- `chief_quality_manager.py` (maschinelle Prüfung)

---

## 📦 CLAWHUB-SKILLS

**Empfohlen:**
- Phy Social Post → Insta + FB + TikTok
- Multi-Platform Scheduler
- Outfeed → Bulk-Publishing

### Lokale Skills (nicht via Jules!)
- **Installiert:** `turkish-native`, `planning-with-files`
- **Sofort relevant:** Marketing Skills (Corey Haines), Stop Slop
- **Speicherort:** `C:\Users\Admin\.agents\skills\`
- Installation: `npx skills add <autor>/<skill-name>`

---

## 🔧 TOOL-WORKFLOW (Jules + Codex + Claude Code)

### Jules (Google)
- 15 Sessions/Tag (rolling 24h), max 3 parallel
- Automatische PRs
- **Neuer Auftrag = neuer Chat**
- **Prinzip:** Ein Auftrag nach dem anderen

### Codex (ChatGPT Plus)
- Nutzungslimit, Reset ~18:41 Uhr
- Kann GitHub-PRs anlegen
- Selbst-enthaltende Aufträge
- **Haupt-Tool für Fixes**

### Claude Code (lokal, über OmniRoute → NVIDIA)
- Kostenlos über NVIDIA Free Tier
- Für Video-Schnitt (FFmpeg oder MCP) und lokale Projekte

### Aufteilung
- **Jules:** Größere Tasks
- **Codex:** Fixes, kleine PRs
- **Claude Code:** Video, lokale Arbeit
- **Nie dieselbe Datei gleichzeitig bearbeiten**

---

## ⚠️ WICHTIGE REGELN

### Verbotene Clubs (nie erwähnen)
- ❌ Osmanen Germania
- ❌ Turkos MC
- ❌ Black Jackets

### Content-Regeln
- ✅ Immer Türkisch + Deutsch
- ✅ Nur öffentliche Infos
- ✅ Respektvoll & positiv
- ✅ Keine politischen Aussagen
- ❌ Keine KI-Deepfakes von echten Personen
- ❌ Keine gekauften Follower / Fake-Follower-Apps
- ❌ Keine Mod-APKs aus unbekannten Quellen

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

### Bekannte technische Fallen

| Problem | Lösung |
|---|---|
| MCP für einfache Aufgaben | FFmpeg nutzen |
| NVIDIA Rate-Limit / 504er | Einzel-Aufträge, Pausen, FFmpeg |
| Streaming-Abbruch | Retry „without streaming" |
| Python < 3.11 | Kinocut braucht 3.11+ |
| Store-Python-Alias | Deaktivieren |
| PATH nach neuer Session | Manuell ergänzen |
| Umlaut in Dateinamen | ASCII-Fallback (staender) |
| Emojis in FFmpeg-Text | Nicht gerendert → weglassen |
| Text-Datei BOM | UTF-8 ohne BOM |
| Windows Admin-PowerShell | User-PATH fehlt → voller Pfad |
| C: chronisch voll | npm-global auf D:, TMP auf D: |
| Kimi K3 + OmniRoute | Streaming-Abbrüche → Nemotron |
| Kaestral + claudeclip gleichzeitig | Nur EINEN Video-MCP |
| OmniRoute Timeout | Env-Vars VOR Start setzen |
| Notepad + JSON | Niemals `.claude.json` mit Notepad |
| Agnes Free-Tier 429 | Cooldown + Fallback |
| force_new_run Haken | Log muss `resolved=true` zeigen |
| Preflight-Selftests | Bei Logik-Änderungen mitpflegen |

---

## 📊 AUTONOMIE-STAND

| Stufe | Status |
|---|---|
| 1. Planung | ✅ |
| 2. Recherche | ✅ |
| 3. Media (Bild/Vision/Translation) | ✅ Phase 1 |
| 4. Compose | ✅ |
| 5. Approval (Telegram + Dashboard) | ✅ |
| 6. Publishing (Insta + FB) | ✅ |
| 7. Publishing (TikTok) | ❌ geplant |
| 8. Media (Audio/Video) | ✅ FFmpeg |
| 9. Engagement (Instagram) | ✅ Agent 17 + Reply Adapter live |
| 10. Engagement (Facebook) | ⏸️ pausiert (Token) |
| 11. Durchgehende Autonomie-Kette | 🟡 Racing-Pipeline ✅, Rest in Arbeit |

**Aktuell: ~70 % autonom.**

---

## 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **Pages:** https://edirne22.github.io/KI-SOCIAL-AGENT/
- **NVIDIA Build:** https://build.nvidia.com/models
- **ClawHub:** https://clawhub.ai
- **Kinocut:** https://pypi.org/project/kinocut/
- **Jules Docs:** https://jules.google/docs/usage-limits/

---

## 🎯 FÜR NEUE CHATS

**Startprompt:**
> „Lies diese drei Dateien der Reihe nach:
> 1. docs/PROJEKT_UEBERGABE.md
> 2. docs/PROJEKT_UEBERGABE_2_ENGAGEMENT.md
> 3. docs/PROJEKT_UEBERGABE_3_RACING.md
>
> Arbeite auf diesem Stand weiter. Bitte alle drei lesen – nicht nach der ersten aufhören."

---

## 🧠 ARBEITS-PRINZIPIEN

### 1. Proaktiv mitdenken
Suboptimales sofort ansprechen.

### 2. Nach jedem Meilenstein: Snapshot
Übergabe ergänzen.

### 3. Bei neuen Chats: Übergabe lesen
Alle Teile der Lese-Kette.

### 4. Modelle/Tools immer hinterfragen
Bessere kostenlose Alternative prüfen.

### 5. Ehrliche Einschätzung > höfliche Zustimmung
Klar ansprechen.

### 6. Komplette Dateien statt Teil-Blöcke
Nie Teil-Blöcke.

### 7. Bei jedem Tool: Öffnungs-Anleitung mitliefern
Windows-Taste → suchen → Enter.

### 8. Konzepte klar abgrenzen
Was es ist / Was nicht / Was Nutzer tun muss / Was automatisch.

### 9. „Pool" statt „To-Do"
Aufgaben sind Pool.

### 10. Multi-KI-Cross-Check (geplant)
Bei wichtigen Entscheidungen mehrere KIs einbeziehen.

### 11. Einfachster Weg zuerst ⚡
FFmpeg/Shell-Einzeiler prüfen bevor komplexe Toolchains.

### 12. Free-Tools-Liste aktiv nutzen
Siehe `docs/FREE_TOOLS.md`.

### 13. Preflight-Selftests sind Verträge
Bei Logik-Änderungen mitpflegen. Sie sind Verträge, keine Deko.

### 14. Technischer QM-Fehler ≠ faktischer QM-Fehler (NEU 26.09.)
Technisch ausgefallener Semantic-Agent darf verifizierte Top-News nicht kommentarlos vernichten. DEGRADED-PASS einführen. Erfundene Fakten bleiben NULL-TOLERANZ.

### 15. Übergabe in Teilen lesen (NEU 26.09.)
Die Übergabe besteht aus 3 Teilen. Alle lesen, nicht nach Teil 1 aufhören.

---

📖 NÄCHSTER TEIL:
→ Lies jetzt: docs/PROJEKT_UEBERGABE_2_ENGAGEMENT.md

Diese Datei ist Teil 1 von 3.
Bitte NICHT anhalten – vollständige Übergabe = alle Teile lesen.
