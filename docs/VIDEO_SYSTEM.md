# 🎬 VIDEO-SYSTEM – Setup & Werkzeuge

**Stand:** 2026-09-22 (Abend)
**Status:** ✅ Erstes Video fertig + gepostet · FFmpeg als Standard etabliert
**Zweck:** Dokumentation der Video-Pipeline – für Reproduktion und Wiederherstellung

---

## 🎯 ZWECK DES SYSTEMS

Bülent steuert Videoschnitt-Aufgaben **per Sprache** – entweder an **FFmpeg** (Standard) oder an **Claude Code mit MCP-Tools** (Sonderfall).

### ⚡ NEUE LEHRE (22.09.2026)

**FFmpeg direkt schlägt MCP-Tools bei einfachen Video-Aufgaben um Längen.**

Der Umweg über Kinocut/claudeclip + OmniRoute + NVIDIA Nemotron kostete **Stunden** (504er, Streaming-Abbrüche, Rate-Limits). Ein FFmpeg-Skript baute den kompletten MotoGP-Reel in **~3 Minuten**.

**Merksatz:** „Wenn's ein Einzeiler kann, nimm den Einzeiler."

### Die Kette – ENTSCHEDUNGSBAUM

```
Aufgabe: Video bauen/schneiden/Text/Musik
           ↓
    ┌──────┴──────┐
    ↓             ↓
EINMALIG?    INTERAKTIV?
(fixem Plan) (viele Varianten,
             Feedback)
    ↓             ↓
FFMPEG        MCP (Claude Code → OmniRoute → NVIDIA → kinocut/claudeclip)
    ↓             ↓
FERTIG        FFmpeg (intern)
```

### 🎯 Wann FFmpeg, wann MCP?

| Aufgabe | Werkzeug |
|---|---|
| **Einmal-Video mit fixem Plan** | **FFmpeg** ✅ |
| **Text-Overlays, Concat, Musik** | **FFmpeg** ✅ |
| **Wiederkehrende Reels, gleiche Struktur** | FFmpeg-Skript mit Variablen |
| **Interaktive Anpassungen, viele Varianten** | MCP (Kinocut/claudeclip) |
| **Video-Generierung aus Text** | KI-Tool (Sora, Runway) – NICHT für Personenfotos |

---

## 🛠️ INSTALLATIONEN (Laptop)

| Komponente | Version | Pfad |
|---|---|---|
| **Node.js** | v24.21.0 | `C:\Program Files\nodejs\` |
| **npm** | 11.19.0 | prefix: `D:\npm-global` |
| **Claude Code** | v2.1.278 | `C:\Users\Admin\AppData\Roaming\npm\claude.cmd` |
| **FFmpeg** | 9.0.2-essentials | `E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin` |
| **Python** | 3.14.7 | `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\` |
| **OmniRoute** | v3.8.50 | `D:\npm-global\node_modules\omniroute\` |
| **claudeclip** | aktuell | `D:\npm-global\node_modules\claudeclip\` |
| **kinocut** | 1.15.1 | über `pip install kinocut` – ~150 Tools |
| **Kaestral** | 1.0.5 | über `npx kaestral` (MCP) |
| **Git** | aktuell | `C:\Program Files\Git\` |

---

## ⚡ FFMPEG-WERKZEUGE (Standard!)

### 📜 Rezept 1 – Reel aus Fotos + Videos bauen

**Skript:** `D:\reel-build.ps1`

**Was es macht:**
- Fotos → Clips mit angegebener Dauer
- Original-Videos → unverändert mit Text-Overlay
- Text-Overlays unten mittig: weiß, fett (arialbd.ttf), 52pt, schwarzer Border 3px
- Concat zu einem Reel

**Text-Dateien:** `build\text-XX.txt` (UTF-8 **ohne BOM**)
**Ausgabe:** `build\reel-final-ohne-musik.mp4`

**Wichtige Filter-Bausteine:**
```
scale=1080:1920:force_original_aspect_ratio=decrease,
pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,
drawtext=fontfile='C\:/Windows/Fonts/arialbd.ttf':
  textfile='…/text-XX.txt':fontcolor=white:fontsize=52:
  borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-th-220
```

### 📜 Rezept 2 – Musik hinzufügen

**Einzeiler** (nach Reel-Build):

```powershell
& "E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe" -y `
  -i "$OUT\reel-final-ohne-musik.mp4" `
  -i "$OUT\musik.m4a" `
  -filter_complex "[1:a]volume=0.2[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]" `
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k `
  "$OUT\reel-final-mit-musik.mp4"
```

**Wirkung:**
- Originalton 100 %, Musik 20 %
- Musik läuft durch den **ganzen** Reel
- Video wird **nicht** neu kodiert → 10 Sek

### 📜 Rezept 3 – Einzelnen Clip neu bauen

**Wenn ein Text falsch ist:**
1. `text-XX.txt` neu schreiben
2. Nur **den einen** Clip rendern (aus Rezept 1, nur ein Block)
3. `concat.txt` neu ausführen

**Dauer:** ~15 Sek, kein Komplettlauf nötig.

### 📌 Wichtige FFmpeg-Details

| Regel | Grund |
|---|---|
| **Emojis weglassen** | Standard-Font rendert sie nicht (leere Kästchen) |
| **Text-Dateien UTF-8 ohne BOM** | Sonst erscheint ein „ï»¿" vor dem Text |
| **Umlaute in Dateinamen vermeiden** | ASCII-Fallback (staender statt ständer) |
| **Font-Pfad mit `C\:`** | Doppelpunkt muss escaped werden |
| **`amix` mit `duration=first`** | Musik nimmt Videolänge, kein Stopp mitten drin |

---

## 🎬 VIDEO-PRODUKTIONS-SYSTEM (MCP – nur wenn nötig)

### Die Kette

```
Claude Code (CLI)
    ↓
OmniRoute (Proxy auf Port 20128)
    ↓
NVIDIA NIM (Nemotron 3.5 Lightning)
    ↓
MCP-Server: kinocut (~150 Tools) ODER claudeclip (31 Tools)
    ↓
FFmpeg
    ↓
Fertige Videos auf D:\SnapShot-Agenten\
```

### ⚠️ Regel: Nur EIN Video-MCP gleichzeitig!

**Nemotron 3.5 Lightning (30B) kann ~35 Tools zuverlässig routen.**
Bei mehr (claudeclip 31 + kaestral 52 = 83) wird es verwirrt und halluziniert.

**Empfehlung:** Nur **einen** Video-MCP aktiv halten.
**Falls größeres Modell verfügbar:** Kaestral reaktivieren und testen.

---

## 🔧 OMNIROUTE SETUP

### Config-Dateien

| Datei | Zweck |
|---|---|
| `C:\Users\Admin\.omniroute\.env` | Haupt-Konfiguration |
| `D:\npm-global\node_modules\omniroute\.env` | Installations-Config |

### Environment-Variablen (VOR Start setzen!)

```
OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS=120000
OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS=120000
```

**Warum:** Standard ist 15000ms (15s) – zu kurz für KI-Tool-Calls.
**Wichtig:** Diese Werte müssen **vor** dem Start gesetzt werden. Dashboard-Einstellung reicht nicht.

### NVIDIA-Provider in OmniRoute

| Feld | Wert |
|---|---|
| **Name** | `NVIDIA NIM` |
| **Präfix** | `nvidia` |
| **API-Typ** | Chat-Abschlüsse |
| **Basis-URL** | `https://integrate.api.nvidia.com/v1` |
| **API-Key** | `nvapi-...` (aus GitHub Secrets: `NVIDIA_API_KEY`) |
| **Modell-ID** | `nvidia/nemotron-3.5-lightning-30b-a3b` |

### Bekannte Modell-Einschränkungen

| Modell | Status |
|---|---|
| `nvidia/nvidia/nemotron-3.5-lightning-30b-a3b` | ✅ **Funktioniert** (Tool-Calling ok) |
| `nvidia/moonshotai/kimi-k3` | ⚠️ Import, aber **Streaming-Problem** |
| `nvidia/nvidia/llama-3.3-nemotron-super-49b-v1.5` | ❌ Nicht im Live-Katalog |
| GLM-4.7, Qwen3 Coder 480B, DeepSeek v4-flash | ❌ EOL bei NVIDIA |

---

## 🚀 CLAUDE CODE STARTSEQUENZ

### Voraussetzungen

**Fenster 1: OmniRoute** muss laufen:

```powershell
# Environment-Variablen setzen (einmal pro PowerShell-Fenster)
$env:OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS="120000"
$env:OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS="120000"

# Server starten
D:\npm-global\omniroute.cmd
```

**Warten bis:** `✔ OmniRoute is running! · Dashboard: http://localhost:20128`
**→ Fenster 1 OFFEN LASSEN.**

### Fenster 2: Claude Code starten

```powershell
$env:PATH = $env:PATH + ";C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts"
cd C:\Users\Admin
$env:ANTHROPIC_BASE_URL="http://localhost:20128"
$env:ANTHROPIC_API_KEY="dein-omni-key"
$env:TMP="D:\ffmpeg-temp"
$env:TEMP="D:\ffmpeg-temp"
C:\Users\Admin\AppData\Roaming\npm\claude.cmd --model "nvidia/nvidia/nemotron-3.5-lightning-30b-a3b"
```

**Beim ersten Start:** Trust-Frage → „Yes, I trust this folder"
**Auto-Mode:** Shift+Tab bis `⏵⏵ auto mode on`

### ⚠️ Wichtige Hinweise

- **Immer als Admin-Shell** – ist bei Bülent Standard
- **User-PATH wird nicht geladen** → `claude` mit vollem Pfad + Python-Scripts-PATH ergänzen
- **Nicht aus `C:\Windows\System32` starten** → erst `cd C:\Users\Admin`
- **Nicht auf `kimi-k3` setzen** → Streaming-Probleme. **Nemotron nutzen.**

---

## 🔌 MCP-SERVER (Claude Code)

### kinocut (1.15.1, ~150 Tools) – im Test

**Python-basiert, guardrailed FFmpeg-Wrapper.**

**Installation:**
```powershell
pip install kinocut
kino doctor
```

**Registrierung:**
```powershell
C:\Users\Admin\AppData\Roaming\npm\claude.cmd mcp add kinocut -- C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts\kino.exe
```

**Erwartet in `kino doctor`:** alle `required`-Checks grün (Kinocut, mcp-server-import, ffmpeg, ffprobe, mcp, pydantic, rich).

### claudeclip (31 Tools) – Standard-Fallback

**Registriert mit:**
```powershell
C:\Users\Admin\AppData\Roaming\npm\claude.cmd mcp add claudeclip -- claudeclip
```

**Tools u.a.:**
- `trim_video` – Video schneiden
- `concat_videos` – Zusammenfügen
- `image_to_video` – Bild zu Video (mit Dauer)
- `add_text_overlay` – Text einblenden
- `add_subtitles` – Untertitel
- `extract_audio` – Audio extrahieren
- `add_audio_track` – Musik hinzufügen

**Test erfolgreich:** Trim von `autogrammToprak.mp4` auf 5 Sek → `test-trim.mp4`, 5.005s, 3.03 MB, ohne Neukodierung.

### Kaestral (52 Tools) – nur wenn nötig

**Registriert mit:**
```powershell
C:\Users\Admin\AppData\Roaming\npm\claude.cmd mcp add kaestral -- cmd /c npx kaestral
```

**Nicht verfügbar unter Windows:** `search_media`, `inspect_color`, `sync_audio`
**Kostenpflichtig (Vorsicht!):** `generate_audio`, `generate_image`, `generate_video`, `upscale_media`

### MCP-Status prüfen

In Claude Code: `/mcp`

**Erwartet (Beispiel):**
```
kinocut · ✓ connected · ~150 tools
```
**oder**
```
claudeclip · ✓ connected · 31 tools
```

**Wichtig:** Immer nur **einer** aktiv!

### MCP-Registrierung unter Windows

```
claude mcp add <name> -- cmd /c npx <paket>
```
**Niemals** `.claude.json` mit Notepad bearbeiten → JSON-Fehler.

---

## 🎬 FFMPEG

### Installation

| Was | Pfad |
|---|---|
| **Binary** | `E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe` |
| **In PATH eingetragen** | ✅ (User-PATH) |

### Prüfen

```powershell
Get-Command npx, ffmpeg -ErrorAction SilentlyContinue
```

---

## 📁 WICHTIGE PFADE

| Was | Pfad |
|---|---|
| **MotoGP-Material** | `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\` |
| **Build-Ordner** | `…\MotoGP-Assen2026\build\` |
| **Fertiger Reel** | `…\build\reel-final-mit-musik.mp4` |
| **Build-Skript** | `D:\reel-build.ps1` |
| **SnapShot-Agenten (Root)** | `D:\SnapShot-Agenten\` |
| **npm-Pakete** | `D:\npm-global\node_modules\` |
| **Python-Scripts** | `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts\` |
| **OmniRoute-Dashboard** | `http://localhost:20128` |
| **Claude-Code-Config** | `C:\Users\Admin\.claude.json` |
| **MCP-Registry** | `C:\Users\Admin\.claude.json` [project: C:\Users\Admin] |

---

## ⚠️ BEKANNTE TECHNISCHE FALLEN

### 1. MCP für einfache Aufgaben (Lehre 22.09.)
**Problem:** Stunden mit MCP verbracht, Rate-Limits, 504er.
**Lösung:** FFmpeg-Einzeiler nutzen. MCP nur wenn interaktiv/Varianten.

### 2. NVIDIA Rate-Limit / 504er
**Problem:** 504-Fehler nach Timeout.
**Lösung:** Env-Vars `MAX_WAIT_MS=120000` setzen · Einzel-Aufträge · Pausen · oder FFmpeg.

### 3. Streaming-Abbruch
**Problem:** „Streaming response ended before any complete data"
**Lösung:**
- Claude Code retryt automatisch „without streaming" (attempt X/10)
- Kimi K3 meiden → **Nemotron 3.5 Lightning** nutzen

### 4. Admin-PowerShell + User-PATH
**Problem:** PowerShell öffnet immer als Admin → `claude` wird nicht gefunden.
**Lösung:** Voller Pfad + Python-Scripts-PATH ergänzen (siehe Startsequenz).

### 5. Python-Version
**Problem:** Kinocut braucht Python 3.11+.
**Lösung:** Python 3.14 funktioniert (getestet). Store-Alias deaktivieren unter „App-Ausführungsaliase".

### 6. Emojis in FFmpeg-Text
**Problem:** Werden nicht gerendert (leere Kästchen).
**Lösung:** Emojis weglassen, nur Text.

### 7. Text-Datei mit BOM
**Problem:** „ï»¿" erscheint vor dem Text.
**Lösung:** UTF-8 **ohne BOM** schreiben (`New-Object System.Text.UTF8Encoding $false`).

### 8. Umlaute in Dateinamen
**Problem:** FFmpeg findet Dateien mit Umlauten nicht immer.
**Lösung:** ASCII-Fallback (staender statt ständer).

### 9. Speicherplatz C:
**Problem:** C: chronisch knapp
**Lösung:** npm-global auf `D:\npm-global` · TMP auf `D:\ffmpeg-temp` · Downloads auf D:

### 10. gptcc funktioniert nicht
**Problem:** ChatGPT Plus + gptcc → 400-Fehler
**Lösung:** Nicht nutzen.

---

## 🎯 GETESTETE BEFEHLE

### ✅ Fertiggestellt

**MotoGP-Reel 22.09.2026:**
- 8 Szenen · 65 Sek · 1080x1920 · 30fps
- Build via `D:\reel-build.ps1` + Musik-Einzeiler
- Fertig: `build\reel-final-mit-musik.mp4`
- Gepostet auf Instagram + Facebook

**Prinzip:**
1. `reel-build.ps1` ausführen → `reel-final-ohne-musik.mp4`
2. Musik-Einzeiler ausführen → `reel-final-mit-musik.mp4`

### 🔄 In Arbeit / Geplant

**Reel 2 – Bikertreff-Runde** (Storyboard steht)
**Reel 3 – Hagen Biker Treff**
**Reel 4 – M1000R-Realität**
**Reel 5 – BiggeGrill**

---

## 🚦 TAGES-START-ROUTINE

**1. Fenster 1 – OmniRoute:**
```powershell
$env:OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS="120000"
$env:OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS="120000"
D:\npm-global\omniroute.cmd
```

**2. Warten:** „✔ OmniRoute is running!"

**3. Fenster 2 – Claude Code:**
```powershell
$env:PATH = $env:PATH + ";C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts"
cd C:\Users\Admin
$env:ANTHROPIC_BASE_URL="http://localhost:20128"
$env:ANTHROPIC_API_KEY="dein-omni-key"
$env:TMP="D:\ffmpeg-temp"
$env:TEMP="D:\ffmpeg-temp"
C:\Users\Admin\AppData\Roaming\npm\claude.cmd --model "nvidia/nvidia/nemotron-3.5-lightning-30b-a3b"
```

**4. In Claude Code prüfen:** `/mcp` → Video-MCP `connected`?

**5. Dann arbeiten.**

**⚡ NEU:** Erst prüfen, ob FFmpeg reicht. MCP nur wenn's sein muss.

---

## 🔄 FALLBACK-STRATEGIE (4 Ebenen!)

| Ebene | Tool | Wann |
|---|---|---|
| **0 – Standard** | **FFmpeg-Skript** | **Bei einfachen Aufgaben** |
| **1 – Primär** | claudeclip + Claude Code | Wenn KI-Schnitt gewünscht |
| **2 – Fallback** | Kinocut + Claude Code | Wenn claudeclip fehlschlägt |
| **3 – Notfall** | OpenReel (Browser) | Wenn alles ausfällt |

**OpenReel:** `https://app.openreel.video/#/editor`

---

## ⚠️ NICHT NUTZEN

- ❌ **MCP für Einmal-Aufgaben** (FFmpeg reicht)
- ❌ **gptcc** (ChatGPT Plus nicht verfügbar für Codex-Modelle)
- ❌ **Kimi K3 + OmniRoute** (Streaming-Probleme)
- ❌ **Mehrere Video-MCPs gleichzeitig** (verwirrt Nemotron)
- ❌ **Kein Video aus `C:\Windows\System32` starten** → erst `cd C:\Users\Admin`

---

## 📌 API-KEYS

| Key | Wo |
|---|---|
| `NVIDIA_API_KEY` | GitHub Secrets (`KI-SOCIAL-AGENT-v2`) |
| **OmniRoute-Key** | Dashboard → API Manager → Notepad |
| **OmniRoute Dashboard-Login** | `admin` / aus `.env` (`INITIAL_PASSWORD`) |

**Sicherheit:**
- Keys NUR in GitHub Secrets + OmniRoute-Dashboard
- Nicht in Chats posten
- Bei Verdacht auf Leak → sofort rotieren

---

## 📊 STATUS

| Komponente | Status |
|---|---|
| OmniRoute | ✅ Läuft |
| NVIDIA-Provider | ✅ Verbunden |
| Nemotron 3.5 Lightning | ✅ Funktioniert |
| claudeclip MCP | ✅ 31 Tools (Fallback) |
| kinocut MCP | ✅ installiert + getestet (1.15.1) |
| Kaestral MCP | ⚠️ pausiert (verwirrt Nemotron) |
| FFmpeg | ✅ Installiert + im Einsatz |
| **FFmpeg-Skript** | ✅ **funktioniert** (Reel 1 bewiesen) |
| **MotoGP-Reel** | ✅ **fertig + gepostet** |

---

## 📌 NÄCHSTE SCHRITTE

1. ✅ MotoGP-Reel 1 – fertig
2. 🔴 Reel 2: Bikertreff-Runde (Radevormwald + Biggesee)
3. 🔴 Reel 3: Hagen Biker Treff
4. 🔴 Reel 4: M1000R-Realität
5. 🔴 Reel 5: BiggeGrill
6. 🟢 Optional: OmniRoute auf VPS (für 24/7-Betrieb)
7. 🟢 Optional: Setup-Backup (`.claude.json`, `.omniroute\.env`) auf D:

---

## 🎬 VIDEO-MCP-TOOLS – ROADMAP

### ✅ Funktioniert

| Tool | Status | Tools | Notiz |
|---|---|---|---|
| **FFmpeg (direkt)** | ✅ **Standard** | – | **Primär – 22.09. bewiesen** |
| **claudeclip** | ✅ live | 31 | Fallback – getestet 21.09. |
| **kinocut** | ✅ installiert | ~150 | Im Test – 22.09. erstmals benutzt |
| **Kaestral** | ⚠️ pausiert | 52 | Verwirrt Nemotron → entfernt |

### 🔄 Zu testen

| Tool | Typ | Warum |
|---|---|---|
| **CutAI** | MCP-Server (Node) | „Agent Mode" mit Selbstbewertung |

### ❌ Ausgeschlossen

| Tool | Grund |
|---|---|
| **MakeMyClip/editor** | Repo existiert nicht |
| **gptcc** | ChatGPT Plus + Codex-Modelle nicht kompatibel |
| **Palmier Pro** | Nur macOS |

### 🖥️ Fallback (kein MCP)

| Tool | Typ | Wann |
|---|---|---|
| **OpenReel** | Browser (`openreel.video`) | Notfall wenn alles ausfällt |

### 🔗 Indirekt relevant

| Tool | Zweck | Status |
|---|---|---|
| **OmniRoute** | Proxy für Claude Code | ✅ Port 20128 |
| **yt-analysis-mcp** | YouTube-Video-Analyse für Expert Agent | 🔴 zu prüfen |
| **n8n** | Workflow-Automatisierung | 🟢 nach VPS |

### 📌 Erkenntnis 22.09.2026

**Weniger Toolchain = zuverlässiger.** Ein FFmpeg-Skript baute den MotoGP-Reel in 3 Minuten. Der Umweg über MCP + Proxy + NVIDIA kostete Stunden.

**Empfehlung:**
1. **Standard:** FFmpeg-Skript
2. **MCP nur wenn:** interaktive Anpassungen, viele Varianten, Feedback-Schleifen
3. **Bei MCP:** Nur EINEN Video-Server gleichzeitig aktiv halten

---

**Ende Video-System-Dokumentation – Stand 22.09.2026 Abend**
