
# 🎬 VIDEO-SYSTEM – Setup & Backup

**Stand:** 2026-09-21 (Abend)
**Status:** ✅ Erstes Video erfolgreich via KI geschnitten
**Zweck:** Dokumentation der funktionierenden Video-Pipeline für Reproduktion und Wiederherstellung

---

## 🎯 Zweck des Systems

Bülent steuert Videoschnitt-Aufgaben **per Sprache an Claude Code**.
Claude Code ruft MCP-Tools auf, die FFmpeg ausführen.
**Kein manueller Schnitt mehr nötig** – aber Fallback auf OpenReel verfügbar.

### Die Kette

```
Claude Code (CLI)
    ↓
OmniRoute (Proxy auf Port 20128)
    ↓
NVIDIA NIM (Nemotron 3.5 Lightning)
    ↓
MCP-Server: claudeclip (31 Tools) → FFmpeg
MCP-Server: kaestral (52 Tools) → FFmpeg
    ↓
Fertige Videos auf D:\SnapShot-Agenten\
```

---

## 🛠️ INSTALLATIONEN (Laptop)

### Was installiert ist

| Komponente | Version | Pfad |
|---|---|---|
| **Node.js** | v24.21.0 | `C:\Program Files\nodejs\` |
| **npm** | 11.19.0 | prefix: `D:\npm-global` |
| **Claude Code** | v2.1.278 | `C:\Users\Admin\AppData\Roaming\npm\claude.cmd` |
| **FFmpeg** | 9.0.2-essentials | `E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin` |
| **OmniRoute** | v3.8.50 | `D:\npm-global\node_modules\omniroute\` |
| **claudeclip** | aktuell | `D:\npm-global\node_modules\claudeclip\` |
| **Kaestral** | 1.0.5 | über `npx kaestral` (MCP) |
| **Git** | aktuell | `C:\Program Files\Git\` |

---

## 🔧 OMNIROUTE SETUP

### Config-Dateien

| Datei | Zweck |
|---|---|
| `C:\Users\Admin\.omniroute\.env` | Haupt-Konfiguration |
| `D:\npm-global\node_modules\omniroute\.env` | Installations-Config |

### Environment-Variablen (beim Start setzen)

```
OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS=60000
OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS=60000
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
| **Modell-ID** | `moonshotai/kimi-k3` (Import), `nvidia/nemotron-3.5-lightning-30b-a3b` |

### Bekannte Modell-Einschränkungen

| Modell | Status |
|---|---|
| `nvidia/moonshotai/kimi-k3` | ✅ Import, aber **Streaming-Problem** |
| `nvidia/nvidia/nemotron-3.5-lightning-30b-a3b` | ✅ **Funktioniert** (Tool-Calling ok) |
| `nvidia/nvidia/llama-3.3-nemotron-super-49b-v1.5` | ❌ Nicht im Live-Katalog |
| `moonshotai/kimi-k2.6` | ✅ Built-in, ungetestet |
| GLM-4.7, Qwen3 Coder 480B | ❌ EOL bei NVIDIA |

---

## 🚀 CLAUDE CODE STARTSEQUENZ (mit OmniRoute)

### Voraussetzungen

**Fenster 1: OmniRoute** muss laufen:
```powershell
# Environment-Variablen setzen (einmal pro PowerShell-Fenster)
$env:OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS="60000"
$env:OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS="60000"

# Server starten
D:\npm-global\omniroute.cmd
```

**Warten bis:**
```
✔ OmniRoute is running!
   Dashboard: http://localhost:20128
```

**→ Fenster 1 OFFEN LASSEN.**

### Fenster 2: Claude Code starten

```powershell
cd C:\Users\Admin
$env:ANTHROPIC_BASE_URL="http://localhost:20128"
$env:ANTHROPIC_API_KEY="dein-omni-key"
C:\Users\Admin\AppData\Roaming\npm\claude.cmd --model "nvidia/nvidia/nemotron-3.5-lightning-30b-a3b"
```

**Beim ersten Start:** Trust-Frage → „Yes, I trust this folder"

### ⚠️ Wichtige Hinweise

- **Immer als Admin-Shell** – ist bei Bülent Standard
- **User-PATH wird nicht geladen** → `claude` muss mit vollem Pfad aufgerufen werden
- **Nicht aus `C:\Windows\System32` starten** → erst `cd C:\Users\Admin`
- **Nicht auf `kimi-k3` setzen** → Streaming-Probleme. **Nemotron nutzen.**

---

## 🔌 MCP-SERVER (Claude Code)

### claudeclip (31 Tools)

**Registriert mit:**
```
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

**Test erfolgreich:**
```
Nutze claudeclip, um autogrammToprak.mp4 auf 5 Sekunden zu trimmen.
```
→ Ergebnis: `test-trim.mp4`, 5.005s, 3.03 MB, keine Neukodierung.

### kaestral (52 Tools)

**Registriert mit:**
```
C:\Users\Admin\AppData\Roaming\npm\claude.cmd mcp add kaestral -- cmd /c npx kaestral
```

**Tools u.a.:**
- `detect_scenes` – Szenen-Erkennung
- `add_clips`, `add_texts`, `add_captions`
- `export_project` – Export als Video/XML/SRT

**Nicht verfügbar unter Windows:**
- `search_media`, `inspect_color`, `sync_audio`

**Kostenpflichtig (Vorsicht!):**
- `generate_audio`, `generate_image`, `generate_video`, `upscale_media`

### MCP-Status prüfen

In Claude Code:
```
/mcp
```

**Erwartet:**
```
claudeclip · ✓ connected · 31 tools
kaestral · ✓ connected · 52 tools
```

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

**Erwartet:**
```
npx.ps1     → C:\Program Files\nodejs\
ffmpeg.exe  → E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin
```

### Für claudeclip

claudeclip bringt **eigenes FFmpeg** mit (`ffmpeg-static` npm-Paket).
Wenn das fehlt → installieren mit:
```
npm install -g --allow-scripts=ffmpeg-static claudeclip
```

---

## 📁 WICHTIGE PFADE

| Was | Pfad |
|---|---|
| **MotoGP-Material** | `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\` |
| **SnapShot-Agenten (Root)** | `D:\SnapShot-Agenten\` |
| **npm-Pakete** | `D:\npm-global\node_modules\` |
| **OmniRoute-Dashboard** | `http://localhost:20128` |
| **Claude-Code-Config** | `C:\Users\Admin\.claude.json` |
| **MCP-Registry** | `C:\Users\Admin\.claude.json` [project: C:\Users\Admin] |

---

## ⚠️ BEKANNTE TECHNISCHE FALLEN

### 1. Admin-PowerShell + User-PATH
**Problem:** PowerShell öffnet immer als Admin → `claude` wird nicht gefunden.
**Lösung:** Voller Pfad: `C:\Users\Admin\AppData\Roaming\npm\claude.cmd`

### 2. OmniRoute Timeout
**Problem:** 504-Fehler nach 15 Sek.
**Lösung:** Env-Variablen vor Start setzen (siehe oben).

### 3. Streaming-Abbruch
**Problem:** „Streaming response ended before any complete data"
**Lösung:**
- Kimi K3 meiden → **Nemotron 3.5 Lightning** nutzen
- API-Key auf „legacy" Modus stellen

### 4. Modell nicht im Live-Katalog
**Problem:** `not available in active live catalog`
**Lösung:**
- Im OmniRoute-Dashboard: **„Import aus /models"** klicken
- Dann Modell suchen + aktivieren

### 5. Speicherplatz C:
**Problem:** C: chronisch knapp
**Lösung:**
- npm-global auf `D:\npm-global` (bereits umgestellt)
- Downloads auf D: umleiten
- Große Ordner (`.cache`, SnapShot-Agenten) auf D: verschieben

### 6. gptcc funktioniert nicht
**Problem:** ChatGPT Plus + gptcc → 400-Fehler
**Grund:** `gpt-5.4` und `gpt-5.4-mini` seit 31.08.2026 nicht für Codex mit ChatGPT verfügbar
**Lösung:** Nicht nutzen. Alternative: Anthropic API direkt oder anderes Modell.

---

## 🎯 GETESTETE BEFEHLE

### ✅ Funktioniert

**Video trimmen:**
```
Nutze claudeclip, um D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\autogrammToprak.mp4 auf die ersten 5 Sekunden zu trimmen.
Speichere als D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\test-trim.mp4
```
**Ergebnis:** ✅ 5.005s, 3.03 MB, ohne Neukodierung.

### 🔄 In Arbeit

**Bild zu Video + zusammenfügen (Reel Teil 1):**
```
Nutze claudeclip, um einen Reel-Clip zu erstellen:
Schritt 1: Wandle gruppenselfieModerator.jpg in 4-Sekunden-Clip um.
Schritt 2: Füge autogrammToprak.mp4 komplett hinzu.
Ausgabe: reel-teil1.mp4
```

### 📋 Geplant

**Reel-Teile 2, 3, 4:**
- Teil 2: `toprak-selfie.jpg` + `toprak-dankesagen.mp4`
- Teil 3: `ich-herowalk.jpg` + `strecke.jpg` + `MotoGP-ständer.jpg` + `toprak-selfie.jpg` (CTA)
- Teil 4: Alle Teile zusammenfügen → `reel-final.mp4`
- Danach: Text-Overlays + Voiceover + Musik

---

## 🚦 TAGES-START-ROUTINE

**Jeden Morgen / nach Neustart:**

1. **Fenster 1 – OmniRoute:**
```powershell
$env:OMNIROUTE_RESILIENCE_REQUEST_QUEUE_MAX_WAIT_MS="60000"
$env:OMNIROUTE_REQUEST_QUEUE_MAX_WAIT_MS="60000"
D:\npm-global\omniroute.cmd
```

2. **Warten:** „✔ OmniRoute is running!"

3. **Fenster 2 – Claude Code:**
```powershell
cd C:\Users\Admin
$env:ANTHROPIC_BASE_URL="http://localhost:20128"
$env:ANTHROPIC_API_KEY="dein-omni-key"
C:\Users\Admin\AppData\Roaming\npm\claude.cmd --model "nvidia/nvidia/nemotron-3.5-lightning-30b-a3b"
```

4. **In Claude Code prüfen:**
```
/mcp
```
→ claudeclip + kaestral als `connected`?

5. **Dann arbeiten.**

---

## 🔄 FALLBACK-STRATEGIE (3 Ebenen)

| Ebene | Tool | Wann |
|---|---|---|
| **1 – Primär** | claudeclip + Claude Code | Standard |
| **2 – Fallback** | Kaestral + Claude Code | Wenn claudeclip fehlschlägt |
| **3 – Notfall** | OpenReel (Browser) | Wenn KI-Schnitt nicht läuft |

**OpenReel:** `https://app.openreel.video/#/editor`

---

## ⚠️ NICHT NUTZEN

- ❌ **gptcc** (ChatGPT Plus nicht verfügbar für Codex-Modelle)
- ❌ **budgetai + Kimi K3** (funktioniert nicht zuverlässig)
- ❌ **OmniRoute + Kimi K3** (Streaming-Probleme)
- ❌ **Kein Video aus C:\Windows\System32 starten** → erst `cd C:\Users\Admin`

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
| claudeclip MCP | ✅ 31 Tools |
| kaestral MCP | ✅ 52 Tools |
| FFmpeg | ✅ Installiert |
| Video-Test | ✅ Erfolgreich |
| MotoGP-Reel | 🔄 In Arbeit |

---

## 📌 NÄCHSTE SCHRITTE

1. 🔄 Reel Teil 1 bauen (Bild + Video zusammenfügen)
2. 🔴 Reel Teile 2–4
3. 🔴 Text-Overlays + Voiceover + Musik
4. 🔴 Export + Posten
5. 🟢 Optional: OmniRoute auf VPS (für 24/7-Betrieb)
6. 🟢 Optional: Setup-Backup (`.claude.json`, `.omniroute\.env`) auf D:

---

**Ende Video-System-Dokumentation.**
