# PROJEKT-ÜBERGABE – KI-SOCIAL-AGENT

**Stand:** 2026-09-22 (Abend)
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
```
🏍️ Strecken-Check für heute (21.09.2026)
✅ Radevormwald (11 Uhr): 11°C, Mäßig bewölkt, gute Bedingungen
✅ Biggesee (11 Uhr): 10°C, Mäßig bewölkt, gute Bedingungen
✅ Sägewerk (11 Uhr): 11°C, Mäßig bewölkt, gute Bedingungen
```

---

## 🎯 PATTERN LIBRARY (Instagram-Content-Bausteine)

**Datei:** `config/PATTERN_LIBRARY.md`
**Stand:** 21.09.2026 – **14 Patterns aktiv**

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
| 12 | Paid vs Free Vergleich | @aitoolswithpritham |
| 13 | Step-by-Step Tutorial | @aiagently |
| 14 | X Free Tools-Liste | @infinity_digitals_official |

**Ziel:** 15–20 Patterns bis Ende Oktober 2026.

**Referenz-Accounts zum Beobachten:**
- @startup_rules (verifiziert)
- @mauryavanshi_edits
- @karishmaticmarketer
- @bitbyybit
- @rakeshmahantiai
- @aitoolswithpritham (verifiziert)
- @aiagently (verifiziert)

**Bonus in Pattern Library:**
- Tool-Alternativen-Sektion (kostenlose Tools)
- KI-Rollen-Bibliothek (15 Rollen aus @alpedya)

---

## 📺 MOTOGP CONTENT PIPELINE (V8.5.5)

### Workflows
| Workflow | Trigger | Zweck |
|---|---|---|
| `motogp-content-agency.yml` | schedule + workflow_dispatch | 5 Tagesvorschläge generieren |
| `motogp-telegram-approval.yml` | **nur workflow_dispatch** | Empfängt MotoGP-Kommandos |
| `telegram-receive.yml` | schedule alle 2 Min (6–21 Uhr) | Zentraler Router |
| `motogp-pipeline-diagnose.yml` | workflow_dispatch | Diagnose |
| `motogp-roster-update.yml` | schedule | Fahrer-Roster aktualisieren |

### Telegram-Befehle
- `motogp 1–5` – einzelne Auswahlen freigeben
- `motogp alle` – alle freigeben
- `motogp nein` – alle ablehnen
- **Wichtig:** Leerzeichen nach Komma (`motogp 2, 3`) → Bug bei `motogp 2,3`

### Instagram Zwei-Stufen-Freigabe (NEU 21.09.2026)
- **Facebook:** postet sofort nach Telegram-Freigabe
- **Instagram:** wartet auf zweite Freigabe
  1. Freigabe → Agnes generiert Bild
  2. Bild kommt in Telegram
  3. `bild ✅` → posten
  4. `bild ❌` → neu generieren

### Wichtige Erkenntnisse
- **5 → 3 Stories möglich** wenn FRESHNESS DIAG filtert
- **FRESHNESS DIAG** filtert nach: fresh / old / missing_date / promo_irrelevant
- **SERIES LOCK** in V8.5.5: immutable series + source-fact whitelist

---

## ⚡ FFMPEG-WERKZEUGE (Standard für Video!)

### ⚠️ Kernlehre 22.09.2026
**FFmpeg direkt schlägt MCP-Tools bei einfachen Video-Aufgaben um Längen.**

Der Umweg über Kinocut/claudeclip + OmniRoute + NVIDIA Nemotron kostete **Stunden** (504er, Streaming-Abbrüche, Rate-Limits). Ein FFmpeg-Skript baute den kompletten MotoGP-Reel in **~3 Minuten**.

### 🎯 Wann FFmpeg, wann MCP?

| Aufgabe | Werkzeug |
|---|---|
| **Einmal-Video mit fixem Plan** | **FFmpeg** ✅ |
| **Text-Overlays, Concat, Musik** | **FFmpeg** ✅ |
| **Wiederkehrende Reels, gleiche Struktur** | FFmpeg-Skript mit Variablen |
| **Interaktive Anpassungen, viele Varianten, Feedback-Schleifen** | MCP (Kinocut/claudeclip) |
| **Video-Generierung aus Text** | KI-Tool (Sora, Runway) – NICHT für Personenfotos |

### 📜 Fertige Skripte & Rezepte

**1. Reel-Build-Skript:** `D:\reel-build.ps1`
- Baut aus Fotos/Original-Videos einen kompletten Reel mit Text-Overlays
- Text-Dateien (UTF-8 ohne BOM) in `build\text-XX.txt`
- Text-Style: weiß, fett (`arialbd.ttf`), 52pt, schwarzer Border 3px, unten mittig
- Ausgabe: `build\reel-final-ohne-musik.mp4`

**2. Musik-Befehl** (Einzeiler):
```powershell
& "E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe" -y -i "$OUT\reel-final-ohne-musik.mp4" -i "$OUT\musik.m4a" -filter_complex "[1:a]volume=0.2[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k "$OUT\reel-final-mit-musik.mp4"
```

**3. Einzel-Clip neu bauen** (falls Text falsch):
- Text-Datei neu schreiben + nur den einen Clip rendern + Concat wiederholen
- Dauert 15 Sek, kein Komplettlauf nötig

### 📌 Wichtige FFmpeg-Details
- **Emojis funktionieren NICHT** mit dem Standard-Font → weglassen
- **Text-Dateien müssen UTF-8 ohne BOM** sein
- **Umlaute in Dateinamen** vermeiden (ASCII-Fallback: staender statt ständer)
- **Font-Pfad** in Filter: `C\:/Windows/Fonts/arialbd.ttf` (Doppelpunkt escaped)
- **`amix` mit `duration=first`** → Musik nimmt Videolänge

---

## 🎬 VIDEO-PRODUKTIONS-SYSTEM (MCP – nur wenn FFmpeg nicht reicht)

**Komplette Kette:**
```
Claude Code → OmniRoute (Port 20128) → NVIDIA NIM (Nemotron 3.5 Lightning)
→ MCP: kinocut (~150 Tools) ODER claudeclip (31 Tools) → FFmpeg → Videos
```

### 🛠️ Installationen auf Bülents Laptop

| Was | Version | Pfad |
|---|---|---|
| **Node.js** | v24.21.0 | C:\Program Files\nodejs\ |
| **npm** | 11.19.0 | prefix: D:\npm-global |
| **OmniRoute** (Proxy) | v3.8.50 | D:\npm-global\omniroute.cmd |
| **Claude Code** | v2.1.278 | C:\Users\Admin\AppData\Roaming\npm\claude.cmd |
| **FFmpeg** | 9.0.2-essentials | E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin |
| **Python** | 3.14.7 | C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\ |
| **claudeclip** | aktuell | D:\npm-global\node_modules\claudeclip\ |
| **kinocut** | 1.15.1 | Python 3.14 – ~150 Tools, `kino doctor` grün |
| **Kaestral** | 1.0.5 | MCP-Server – Fallback, nur wenn nötig |

### 🔧 OmniRoute-Konfiguration (Port 20128)

**Startdatei:** `D:\npm-global\omniroute.cmd`

**Env-Vars VOR Start setzen (Dashboard reicht NICHT):**
```
OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS=120000
OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS=120000
```

**NVIDIA-Provider in OmniRoute:**
- Präfix: `nvidia`
- Modell: `nvidia/nvidia/nemotron-3.5-lightning-30b-a3b`
- Base-URL: `https://integrate.api.nvidia.com/v1`

**Achtung:** GLM-4.7, Qwen3 Coder 480B, DeepSeek v4-flash sind auf NVIDIA NIM **EOL**.

### 🚀 Claude Code Startsequenz (WICHTIG – immer so!)

**Problem:** PowerShell öffnet bei Bülent **immer als Admin** → User-PATH wird nicht geladen.

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

**Auto-Mode aktivieren:** Shift+Tab bis `⏵⏵ auto mode on`

**Nicht aus `C:\Windows\System32` starten!** → „No, exit" wählen, dann `cd C:\Users\Admin`.

### 🎬 Video-MCPs (nur EINER gleichzeitig aktiv!)

**kinocut** (1.15.1, ~150 Tools) – im Test
- Python-basiert, guardrailed FFmpeg-Wrapper
- Braucht Python 3.11+ (auf 3.14 läuft's)
- Installation: `pip install kinocut` → `kino doctor` prüfen
- Registrierung: `claude mcp add kinocut -- C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts\kino.exe`

**claudeclip** (31 Tools) – Standard-Fallback
- Relevante Tools: `trim_video`, `concat_videos`, `image_to_video`, `add_text_overlay`, `add_subtitles`, `extract_audio`, `add_audio_track`

**Kaestral** (52 Tools) – nur wenn nötig
- ⚠️ Verwirrt Nemotron (zu viele Tools) → temporär entfernt
- **Nicht verfügbar unter Windows:** `search_media`, `inspect_color`, `sync_audio`
- **Kostenpflichtig (nicht ohne Freigabe):** `generate_audio`, `generate_image`, `generate_video`, `upscale_media`
- Registrierung: `claude mcp add kaestral -- cmd /c npx kaestral`

**⚠️ Regel:** Niemals zwei Video-MCPs gleichzeitig aktiv → überlastet Nemotron.

**MCP-Registrierung (Windows):**
```
claude mcp add <name> -- cmd /c npx <paket>
```
**Niemals** `.claude.json` mit Notepad bearbeiten → JSON-Fehler.

### 📁 MotoGP-Material-Pfad

**Ordner:** `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026`
**Build-Ordner:** `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\build`

---

## 🎬 CONTENT-MATERIAL (Übersicht)

### 5 Foto-/Video-Ordner auf Laptop

| Ordner | Inhalt | Potenzial |
|---|---|---|
| **MotoGP Assen 2026** | Toprak, Jack Miller, Morbidelli, Rins, Ai Ogura, Strecke, Stände | 🔥 höchstes |
| **Radevormwald** | Fotos | mittel |
| **BiggeGrill / Biggesee** | Fotos | mittel |
| **Hagen Biker Treff** | Fotos | mittel |
| **M1000R Übungsplatz** | Kreise, Achten, Reifen, Helm | hoch |

### 🏆 Top-Material: MotoGP Assen 2026
- 🎥 Toprak-Video (Dank auf Türkisch)
- 🎥 Autogramm-Video (Unterschrift auf Shirt)
- 🎥 Moderator-Video (Englisch)
- 📸 Gruppenselfie mit Moderator + Helfer + Damian
- 📸 Selfies mit Toprak, Jack Miller, Morbidelli, Rins
- 📸 Strecke + Stände

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
| 4 | toprak-dankesagen.mp4 | 7s | „Danke Toprak" (Original-Ton laut!) |
| 5 | ich-herowalk.jpg | 5s | „Hero Walk – hautnah" |
| 6 | strecke.jpg | 5s | „Assen 2026 – die Strecke" |
| 7 | MotoGP-ständer.jpg | 4s | „Die MotoGP-APP" |
| 8 | toprak-selfie.jpg | 5s | „Teil 2 folgt – wer ist euer Favorit?" |

**Emojis wurden weggelassen** (FFmpeg-Standard-Font).

### Post-Caption (Türkisch + Deutsch)

Deutsch:
> Unfassbar. 🤯
> Wir waren in Assen – und plötzlich standen wir neben Toprak Razgatlıoğlu. Ein Moderator kam auf uns zu, fragte, ob wir zu ihm wollen. Klar wollten wir! Autogramm aufs Shirt, Selfie mit dem Weltmeister – und er hat sich sogar auf Türkisch bedankt. 🇹🇷
> Welcher Fahrer ist euer Favorit? Schreibt's in die Kommentare! 👇

Türkçe:
> İnanılmaz! 🤯
> Assen'deydik – ve bir anda kendimizi Toprak Razgatlıoğlu'nun yanında bulduk. Bir moderatör yanımıza geldi, "Toprak'a gitmek ister misiniz?" diye sordu. Tabii ki istedik! Formaya imza, dünya şampiyonuyla selfie – hatta Türkçe teşekkür etti. 🇹🇷
> En sevdiğiniz pilot hangisi? Yorumlara yazın! 👇

Hashtags: #MotoGP #MotoGP2026 #Assen #ToprakRazgatlioglu #Motorrad #BikerLife #Motorradfahren #Reels #Motorcycle #Superbike #TurkishBikers #TürkMotorcuları

### 🎯 Reel-Plan (nächste)

| # | Reel | Status |
|---|---|---|
| 1 | MotoGP Assen | ✅ fertig + gepostet |
| 2 | Bikertreff-Runde (Radevormwald + Biggesee) | 🔴 Storyboard fertig |
| 3 | Hagen Biker Treff | ⏸️ wartet |
| 4 | M1000R-Realität | ⏸️ wartet |
| 5 | BiggeGrill | ⏸️ wartet |

---

## 🧠 EXPERT AGENT (Konzept)

**Was es ist:**
Ein Claude-Code-Skill, der aus 10 YouTube-Tutorials trainiert wird und dann bei Aufgaben angewendet wird.

**Was es NICHT ist:**
- Kein kontinuierlich lernender Agent
- Kein autonom suchender Agent
- Kein Feedback-Loop ohne Nutzer

**Ablauf:**
1. Nutzer sammelt 10 YouTube-Links zu einem Thema
2. Claude Code studiert sie (yt-analysis-mcp + Gemini)
3. Skill wird gebaut und als Datei gespeichert
4. Nutzer testet + gibt Feedback
5. Skill wird bei jedem Lauf angewendet

**Geplantes Langzeitgedächtnis:**
- `CLAUDE.md` im Repo-Root (Projekt-Kontext)
- `memory/EXPERT_SKILLS/` Ordner mit pro Skill eine `.md`
- `memory/EXPERT_EVENTS.jsonl` (chronologisches Log)
- Basic Memory MCP (`@basic-memory/mcp-server`)

**Erste Kandidaten:**
- MotoGP-Reel-Schnitt
- Bikertreff-Video-Stil
- Hook-Writer für erste 3 Sek

---

## 🖥️ APPROVAL-DASHBOARD

**Aktuell:** Freigabe über Telegram.

### Stufe 2 – ✅ UMGESETZT (22.09.2026)
- `docs/approval/index.html` – Freigabe-Liste
- `docs/approval/app.js` – Vanilla JS + localStorage
- `docs/approval/style.css` – dunkel, mobil-freundlich
- `docs/approval/queue.json` – Mock-Daten (später vom Publisher-Workflow)
- `.github/workflows/pages.yml` – Deploy bei Push
- URL: `edirne22.github.io/KI-SOCIAL-AGENT/`
- **TODO Stufe 3 im Code:** Entscheidung an Pipeline senden

### Stufe 3 – NACH VPS
- Streamlit oder Next.js
- Kalender, Analytics, Content-Bibliothek
- Echte Persistierung (Backend)

---

## 📦 CLAWHUB-SKILLS

**Empfohlen:**
- **Phy Social Post** → Insta + FB + TikTok
- **Multi-Platform Scheduler**
- **Outfeed** → Bulk-Publishing

### Lokale Skills (nicht via Jules!)
- **Sofort relevant:** Planning with Files, Türkçe Yazı Yazma, Marketing Skills
- Installation: `npx skills add <autor>/<skill-name>`

---

## 🔴 OFFENE PRIORITÄTEN (siehe IDEA_POOL.md)

Alle offenen Aufgaben sind ausgelagert in `docs/IDEA_POOL.md`.

---

## 🔧 TOOL-WORKFLOW (Jules + Codex + Claude Code)

### Jules (Google)
- 15 Sessions/Tag, max 3 parallel
- Automatische PRs
- **Neuer Auftrag = neuer Chat**
- **Prinzip:** Ein Auftrag nach dem anderen, Review vor dem nächsten

### Codex (ChatGPT Plus)
- Nutzungslimit, Reset ~18:41 Uhr
- Kann GitHub-PRs anlegen
- Selbst-enthaltende Aufträge

### Claude Code (lokal, über OmniRoute → NVIDIA)
- Kostenlos über NVIDIA Free Tier
- Für Video-Schnitt (FFmpeg oder MCP) und lokale Projekte
- **Startsequenz siehe oben**

### Aufteilung
- **Jules:** Größere Tasks
- **Codex:** Fixes, kleine PRs
- **Claude Code:** Video, lokale Arbeit
- **Nie dieselbe Datei gleichzeitig bearbeiten**

---

## ⚠️ WICHTIGE REGELN

### Verbotene Clubs (nie erwähnen, nie taggen)
- ❌ Osmanen Germania
- ❌ Turkos MC
- ❌ Black Jackets

### Content-Regeln
- ✅ Immer Türkisch + Deutsch
- ✅ Nur öffentliche Infos
- ✅ Respektvoll & positiv
- ✅ Keine politischen Aussagen
- ❌ Keine KI-Deepfakes von echten Personen

### Branches
- `main` = produktiv
- `debug/motogp-pipeline-output` = nur Bülent + Codex

### Bekannte technische Fallen

| Problem | Lösung |
|---|---|
| **MCP für einfache Aufgaben** | ❌ FFmpeg nutzen (Lehre 22.09.) |
| **NVIDIA Rate-Limit / 504er** | Einzel-Aufträge, Pausen, oder FFmpeg |
| **Streaming-Abbruch** | Claude Code retryt automatisch „without streaming" |
| **Python < 3.11** | Kinocut braucht 3.11+ (auf 3.14 läuft's) |
| **Store-Python-Alias** | Deaktivieren unter „App-Ausführungsaliase" |
| **PATH nach neuer Session** | Manuell ergänzen: Python-Scripts + FFmpeg-Bin |
| **Umlaut in Dateinamen** | ASCII-Fallback (staender) |
| **Emojis in FFmpeg-Text** | Werden nicht gerendert → weglassen |
| **Text-Datei BOM** | Muss UTF-8 ohne BOM sein |
| **Windows Admin-PowerShell** | User-PATH fehlt → voller Pfad |
| **C: chronisch voll** | npm-global auf D:, TMP auf D:\ffmpeg-temp |
| **Kimi K3 + OmniRoute** | Streaming-Abbrüche → Nemotron nutzen |
| **Kaestral + claudeclip gleichzeitig** | Verwirrt Nemotron → nur einen Video-MCP |
| **OmniRoute Timeout** | Env-Vars `MAX_WAIT_MS` VOR Start setzen |
| **Notepad + JSON** | Niemals `.claude.json` mit Notepad bearbeiten |

---

## 📊 AUTONOMIE-STAND

| Stufe | Status |
|---|---|
| 1. Planung | ✅ |
| 2. Recherche | ✅ |
| 3. Media (Bild/Vision/Translation) | ✅ Phase 1 |
| 4. Compose | ⏳ teilweise |
| 5. Approval (Telegram + Dashboard Stufe 2) | ✅ |
| 6. Publishing (Insta + FB) | ✅ |
| 7. Publishing (TikTok) | ❌ geplant |
| 8. Media (Audio/Video) | ✅ **FFmpeg-Skript funktioniert** |
| 9. Durchgehende Autonomie-Kette | 🔴 in Arbeit |

**Aktuell: ~60 % autonom.**

---

## 📎 QUELLEN & LINKS

- **Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
- **PRs:** https://github.com/Edirne22/KI-SOCIAL-AGENT/pulls
- **Actions:** https://github.com/Edirne22/KI-SOCIAL-AGENT/actions
- **Pages:** https://edirne22.github.io/KI-SOCIAL-AGENT/
- **NVIDIA Build:** https://build.nvidia.com/models
- **ClawHub:** https://clawhub.ai
- **Kaestral:** https://github.com/prabindersinghh/Kaestral-pro
- **Kinocut:** https://pypi.org/project/kinocut/
- **OpenReel:** https://openreel.video
- **YouMind:** https://youmind.com
- **PromptCreek:** https://promptcreek.com
- **Handbuch:** `docs/HANDBUCH.md`
- **IDEA POOL:** `docs/IDEA_POOL.md`
- **Snapshot 22.09. Abend:** `docs/SNAPSHOT_2026-09-22_ABEND.md`
- **API-Referenz:** `docs/API_REFERENZ.md`
- **Approval-Dashboard:** `docs/approval/`
- **Bikertreffs:** `config/Bikertreffs.md`
- **Pattern Library:** `config/PATTERN_LIBRARY.md`
- **Jules Docs:** https://jules.google/docs/usage-limits/

---

## 🎯 FÜR NEUE CHATS

**Startprompt für neuen Chat:**
> „Lies `docs/PROJEKT_UEBERGABE.md` im Repo Edirne22/KI-SOCIAL-AGENT (raw: https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/docs/PROJEKT_UEBERGABE.md). Arbeite auf diesem Stand weiter."

---

## 🧠 ARBEITS-PRINZIPIEN (verbindlich für alle Chats)

### 1. Proaktiv mitdenken
Wenn dem Assistenten auffällt, dass etwas **suboptimal** ist, soll er das **sofort ansprechen** – nicht erst auf Nachfrage.

### 2. Nach jedem Meilenstein: Snapshot
Wenn ein größeres Feature fertig ist: Eintrag in Übergabe ergänzen.

### 3. Bei neuen Chats: Übergabe lesen
Der Assistent MUSS zu Beginn die `PROJEKT_UEBERGABE.md` lesen.

### 4. Modelle/Tools immer hinterfragen
Wenn ein Modell/Tool nicht liefert: Bessere kostenlose Alternative prüfen.

### 5. Ehrliche Einschätzung > höfliche Zustimmung
Bei Schwächen, Risiken oder Fehlern: klar ansprechen.

### 6. Komplette Dateien statt Teil-Blöcke
Bei Änderungen: IMMER die komplette Datei liefern, nie Teil-Blöcke.

### 7. Bei jedem Tool: Öffnungs-Anleitung mitliefern
Bülent ist kein Programmierer. Bei Tool-Erwähnung immer:
1. Wie öffnen (Windows-Taste → suchen → Enter)
2. Woran erkennen (Prompt-Anzeige, Fensterfarbe)
3. Wie schließen (Strg+C, /exit, X)

**Negativ:** „Öffne PowerShell" ❌
**Positiv:** „Drücke Windows-Taste → tippe `powershell` → Enter." ✅

### 8. Konzepte klar abgrenzen
Bei neuen Ideen (z.B. Expert Agent) IMMER:
- Was es ist
- Was es NICHT ist
- Was der Nutzer tun muss
- Was automatisch passiert

### 9. „Pool" statt „To-Do"
Aufgaben sind ein Pool zur Auswahl, kein Zwang. Datei: `docs/IDEA_POOL.md`.

### 10. Multi-KI-Cross-Check (geplant)
Bei wichtigen Entscheidungen (Prompts, Pläne, Code) mehrere KIs einbeziehen und die Antworten vergleichen. Tool-Auswahl + Setup siehe `docs/IDEA_POOL.md` → Prio 1 „Multi-KI Cross-Check". Ziel: Kein manuelles Copy-Paste mehr zwischen Chat und Claude Code.

### 11. Einfachster Weg zuerst ⚡ (NEU 22.09.2026)
Bevor komplexe Toolchains (MCP, KI-Agenten, Multi-Service-Setups) aktiviert werden: **prüfen, ob ein FFmpeg/Shell-Einzeiler reicht.**
- **FFmpeg direkt** bei: einmaligen Videos, Text-Overlays, Concat, Musik
- **MCP** nur bei: interaktiven Anpassungen, vielen Varianten, Feedback-Schleifen
- **Lehre vom 22.09.:** Stunden mit MCP verbracht → FFmpeg-Skript baute den Reel in 3 Minuten.
- **Merksatz:** „Wenn's ein Einzeiler kann, nimm den Einzeiler."

### 12. Free-Tools-Liste aktiv nutzen (NEU 23.09.2026)
Bei jedem neuen Content-Stück (Reel, Karussell, Story) und bei
jedem Agenten-Ausbau: prüfen, ob ein Tool aus
`docs/FREE_TOOLS.md` genutzt werden kann.

- **Vor Rückgriff auf kostenpflichtige Tools:** erst Free-Tools-Liste checken
- **Bei jedem neuen Tool:** in die Liste eintragen (Kategorie + Free-Tier-Status)
- **„Aktuell genutzt"-Sektion** oben in `FREE_TOOLS.md` pflegen
- **Seriositäts-Check:** vor Nutzung 30 Sek Google-Suche (Scam-Verdacht ausschließen)
- **Quarterly:** Liste durchgehen, was funktioniert / was nicht

**Ziel:** 0-€-Philosophie halten, nicht in teure Abos rutschen.
---

**Ende Übergabe – Stand 22.09.2026 Abend**
