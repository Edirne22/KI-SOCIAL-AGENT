
# 📸 UMZUG-SNAPSHOT – 22.09.2026 (Abend)

**Für neuen Chat – 1:1 einfügen**

---

## 🎯 PROJEKT

**KI-SOCIAL-AGENT** – Autonome Content-Fabrik für Bülent (@edirnelibuelent)
**Repo:** https://github.com/Edirne22/KI-SOCIAL-AGENT
**Ziel:** Motorrad-Content auf Instagram/Facebook/TikTok, 0 €/Monat
**Vision:** 12–24 Monate zur eigenen KI-Agentur

---

## 🚦 STATUS (22.09. Abend)

### ✅ Heute fertiggestellt

- **MOTOGP-REEL IST FERTIG UND GEPOSTET** 🎬
  - Pfad: `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\build\reel-final-mit-musik.mp4`
  - 65 Sekunden · 1080x1920 · 30fps · 21 MB
  - Post mit Türkisch+Deutsch Caption auf Instagram + Facebook
- **PR #55 gemergt:** `docs/API_REFERENZ.md` (APIs für Weather, Sports, News, Video, Social, Vehicle mit Free-Tier-Spalte)
- **Approval-Dashboard Stufe 2 gemergt:** `docs/approval/` (HTML/JS + localStorage + TODO Stufe 3 im Code) → Ziel: `edirne22.github.io/KI-SOCIAL-AGENT/`
- **Kinocut installiert:** Python 3.14.7, kinocut 1.15.1, `kino doctor` grün, als MCP registriert

### ✅ Läuft automatisch (unverändert)

Weather Agent · MotoGP Content Pipeline · Telegram Vision-Bot · Finanzagent · Follow-Analyzer · Deal-Hunter · Preis-Check · Instagram + Facebook Publisher · Zwei-Stufen-Freigabe

---

## 🎬 VIDEO-SYSTEM – NEUE ERKENNTNIS (wichtig!)

### ⚠️ Kernlehre des Tages

**FFmpeg direkt schlägt MCP-Tools bei einfachen Aufgaben um Längen.**

Der Umweg über Kinocut/claudeclip + OmniRoute + NVIDIA Nemotron kostete **Stunden** (504er, Streaming-Abbrüche, Rate-Limits). Das fertige FFmpeg-Skript baute den kompletten Reel in **~3 Minuten**.

**Neue Regel (muss als Ziffer 11 in Übergabe):**

> **Einfachster Weg zuerst:** Bei Aufgaben prüfen, ob ein FFmpeg/Shell-Einzeiler reicht, bevor komplexe Toolchains (MCP, KI-Agenten) aktiviert werden. MCP nur, wenn's einen echten Grund gibt (interaktive Anpassungen, viele Varianten, Feedback-Schleifen).

### 📜 Fertige FFmpeg-Skripte

**1. Reel-Build-Skript:** `D:\reel-build.ps1`

- Baut aus Fotos/Original-Videos einen kompletten Reel mit Text-Overlays
- Text-Dateien (UTF-8 ohne BOM) in `build\text-XX.txt`
- Text-Style: weiß, fett (`arialbd.ttf`), 52pt, schwarzer Border 3px, unten mittig
- Ausgabe: `build\reel-final-ohne-musik.mp4`

**2. Musik-Befehl** (Einzeiler, in PowerShell):

```powershell
& "E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe" -y -i "$OUT\reel-final-ohne-musik.mp4" -i "$OUT\musik.m4a" -filter_complex "[1:a]volume=0.2[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k "$OUT\reel-final-mit-musik.mp4"
```

**3. Einzel-Clip neu bauen** (falls Text falsch):

- Text-Datei neu schreiben + nur den einen Clip rendern + Concat wiederholen
- Dauert 15 Sek, kein Komplettlauf nötig

### 🎯 Wann MCP (Kinocut/claudeclip), wann FFmpeg?

| Aufgabe | Werkzeug |
|---|---|
| **Einmal-Video mit fixem Plan** | **FFmpeg** |
| **Text-Overlays, Concat, Musik** | **FFmpeg** |
| **Wiederkehrende Reels, gleiche Struktur** | FFmpeg-Skript mit Variablen |
| **Interaktive Anpassungen, viele Varianten, Feedback-Schleifen** | MCP (Kinocut/claudeclip) |
| **Video-Generierung aus Text** | KI-Tool (Sora, Runway) – NICHT für Personenfotos |

### 🔗 Video-Kette (wenn MCP nötig)

```
Claude Code → OmniRoute (Port 20128) → NVIDIA NIM (Nemotron 3.5 Lightning)
→ MCP: kinocut (1.15.1, ~150 Tools) ODER claudeclip (31 Tools) → FFmpeg
```

### Startsequenz (Fenster 1 + 2)

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

→ Trust-Frage „Yes" · Shift+Tab bis `⏵⏵ auto mode on`

---

## 🎬 MOTOGP-REEL – SZENEN (fertig)

| # | Datei | Dauer | Text |
|---|---|---|---|
| 1 | gruppenselfieModerator.jpg | 4s | „Er fragte: Wollt ihr zu Toprak?" |
| 2 | autogrammToprak.mp4 | 24s | „Der Moderator hat's möglich gemacht" |
| 3 | toprak-selfie.jpg | 5s | „Toprak Razgatlioglu" |
| 4 | toprak-dankesagen.mp4 | 7s | „Danke Toprak" (Original-Ton laut!) |
| 5 | ich-herowalk.jpg | 5s | „Hero Walk – hautnah" |
| 6 | strecke.jpg | 5s | „Assen 2026 – die Strecke" |
| 7 | MotoGP-ständer.jpg | 4s | **„Die MotoGP-APP"** (korrigiert!) |
| 8 | toprak-selfie.jpg | 5s | „Teil 2 folgt – wer ist euer Favorit?" |

**Emojis wurden weggelassen** (FFmpeg-Standard-Font kann sie nicht rendern).

---

## 🧠 SKILLS / TOOLS – NEU

### Jules (Google)

- ✅ PR #55 (API-Referenz) gemergt
- ✅ Approval-Dashboard Stufe 2 gemergt
- Prinzip: ein Auftrag nach dem anderen

### Multi-KI Cross-Check (Prio 1 im IDEA_POOL)

- **Ziel:** Kein manuelles Copy-Paste mehr, mehrere KIs einbeziehen
- **Kandidaten:** `claudelink-bridge`, `llm-council-no-api`, `cross-review`
- **Status:** Noch nicht getestet

### Skills (lokal, nicht via Jules)

- **Sofort relevant:** Planning with Files, Türkçe Yazı Yazma, Marketing Skills
- Installation: `npx skills add <autor>/<skill-name>`
- Zeitplan: nach Reel (jetzt aktuell!)

---

## 🐛 TELEGRAM-BUGS

- `/alle` mit Slash → wird nicht erkannt
- `motogp 2,3` → Parser bricht
- Batch-Status-Mismatch (`FREIGEGEBEN` vs `READY_FOR_APPROVAL`)

---

## ⚠️ BEKANNTE FALLEN (erweitert)

| Problem | Lösung |
|---|---|
| **MCP für einfache Aufgaben** | ❌ FFmpeg nutzen (Lehre des Tages!) |
| **NVIDIA Rate-Limit / 504er** | Einzel-Aufträge, Pausen, oder FFmpeg |
| **Streaming-Abbruch** | Claude Code retryt automatisch „without streaming" |
| **Python < 3.11** | Kinocut braucht 3.11+; auf 3.14 funktioniert's |
| **Store-Python-Alias** | Deaktivieren unter „App-Ausführungsaliase" |
| **PATH nach neuer Session** | Manuell ergänzen: Python-Scripts + FFmpeg-Bin |
| **Umlaut in Dateinamen** | ASCII-Fallback (staender) |
| **Emojis in FFmpeg-Text** | Werden nicht gerendert → weglassen |
| **Windows Admin-PowerShell** | User-PATH fehlt → voller Pfad |
| **C: chronisch voll** | npm-global auf D:, TMP auf D:\ffmpeg-temp |
| **Kimi K3 + OmniRoute** | Streaming-Abbrüche → Nemotron nutzen |
| **Kaestral + claudeclip gleichzeitig** | Verwirrt Nemotron → nur einen Video-MCP |
| **OmniRoute Timeout** | Env-Vars `MAX_WAIT_MS` VOR Start setzen |

---

## 📁 WICHTIGE PFADE

| Was | Pfad |
|---|---|
| MotoGP-Material | `D:\SnapShot-Agenten\20260919\MotoGP-Assen2026\` |
| **Fertiger Reel** | `…\build\reel-final-mit-musik.mp4` |
| Build-Skript | `D:\reel-build.ps1` |
| Claude Code | `C:\Users\Admin\AppData\Roaming\npm\claude.cmd` |
| OmniRoute | `D:\npm-global\omniroute.cmd` |
| FFmpeg | `E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\` |
| Kinocut | `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts\kino.exe` |
| npm-Global | `D:\npm-global` |
| OmniRoute-Dashboard | `http://localhost:20128` |

---

## 📄 WICHTIGE DATEIEN IM REPO

- `docs/PROJEKT_UEBERGABE.md` – Hauptübergabe (**Stand 22.09. Mittag** – ggf. ergänzen um Ziffer 11 + FFmpeg-Lehre)
- `docs/VIDEO_SYSTEM.md` – Video-Setup (MCP-lastig – sollte ergänzt werden)
- `docs/IDEA_POOL.md` – Aufgaben-Pool (mit HEUTE-Block oben + Prio 1 Multi-KI)
- `docs/API_REFERENZ.md` – NEU: API-Sammlung mit Free-Tier-Spalte
- `docs/approval/` – NEU: Freigabe-Dashboard Stufe 2
- `config/PATTERN_LIBRARY.md` – 15 Patterns
- `memory/VISION_LOG.jsonl`
- `agents/weather_agent.py`, `agents/vision_summary_agent.py`

---

## 🎯 NÄCHSTE SCHRITTE (morgen / die Tage)

1. **Ziffer 11 in Übergabe** nachtragen: „Einfachster Weg zuerst"
2. **`docs/VIDEO_FFMPEG.md`** anlegen – die 3 FFmpeg-Rezepte dokumentieren
3. **Ziffer 10 in Übergabe** war schon drin: Multi-KI-Cross-Check
4. **Skills installieren** (Planning with Files, Türkçe Yazı Yazma)
5. **Nächster Reel:** Bikertreff-Runde (Radevormwald + Biggesee) – Storyboard steht
6. **Post-Erfolg messen** (Reel 1 auf Insta/FB)

---

## 🚀 STARTPROMPT FÜR NEUEN CHAT

```
Lies docs/PROJEKT_UEBERGABE.md und docs/IDEA_POOL.md.
Ich arbeite am KI-SOCIAL-AGENT (Repo: Edirne22/KI-SOCIAL-AGENT).

Wichtigste Lehre vom 22.09.: FFmpeg direkt > MCP-Tools für einfache
Video-Aufgaben. Reel 1 (MotoGP) ist fertig und gepostet.

Aktueller Fokus: [Ziffer 11 in Übergabe / VIDEO_FFMPEG.md anlegen /
Skills installieren / nächster Reel / ...].

Bitte: einfachster Weg zuerst – bei Aufgaben prüfen, ob FFmpeg/Shell
reicht, bevor komplexe Toolchains aktiviert werden.
```

---

**Ende Snapshot – 22.09.2026 Abend**

---

## 💬 Ehrliche Schlussnotiz

Heute war ein **großer Meilenstein** (erster Reel fertig) – aber auch ein **schmerzhafter Lernprozess**. Die Lehre ist wichtig und steht jetzt schwarz auf weiß im Snapshot: **Bei einfachen Aufgaben erst den einfachen Weg prüfen.** Das gilt für alle zukünftigen Chats.
