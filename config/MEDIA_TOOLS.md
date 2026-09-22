
Aufgabe: Lege die Datei config/MEDIA_TOOLS.md an.

Zweck: Übersicht aller lokalen Medien-Werkzeuge für den
KI-Social-Agent – was kann welches Tool, wann nutzen, wo liegt es.

Struktur:

# MEDIA-TOOLS – Lokale Werkzeuge

## Video
### FFmpeg (Standard)
- Version: 9.0.2-essentials
- Pfad: E:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\
- Wann nutzen: Immer bei Einmal-Aufgaben (Overlays, Concat, Musik)
- Warum Standard: Schnell, zuverlässig, keine Rate-Limits
- Beweis: MotoGP-Reel 22.09. in 3 Minuten gebaut

### claudeclip (MCP)
- Version: aktuell
- Pfad: D:\npm-global\node_modules\claudeclip\
- Registrierung: claude mcp add claudeclip -- claudeclip
- Tools: 31 (trim_video, concat_videos, add_text_overlay, ...)
- Wann nutzen: Fallback wenn FFmpeg-Skript nicht reicht
- Wann NICHT: Einmal-Aufgaben (dauert länger, Rate-Limits)

### kinocut (MCP)
- Version: 1.15.1
- Installation: pip install kinocut (Python 3.11+)
- Pfad: C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Scripts\kino.exe
- Registrierung: claude mcp add kinocut -- [Pfad zu kino.exe]
- Tools: ~150 (guardrailed FFmpeg-Wrapper)
- Wann nutzen: Wenn interaktive Anpassungen nötig

### Kaestral (MCP) – pausiert
- Version: 1.0.5
- Grund Pause: Verwirrt Nemotron (zu viele Tools, 52)
- Nicht verfügbar unter Windows: search_media, inspect_color, sync_audio
- Kostenpflichtig: generate_audio/image/video, upscale_media

WICHTIG: Nur EIN Video-MCP gleichzeitig aktiv!

## Bild
- image_router.py (Pollinations → Cloudflare → Together → NVIDIA → Agnes)

## Audio
- speech_router.py (Nemotron ASR + Magpie TTS) – nach VPS

## Entscheidungsbaum
Aufgabe → Einmalig? → FFmpeg
Aufgabe → Interaktiv/Varianten? → MCP (claudeclip oder kinocut)

## Abgrenzung
Diese Datei = lokale Werkzeuge.
NICHT zu verwechseln mit:
- docs/API_REFERENZ.md (externe Daten-APIs)
- docs/VIDEO_SYSTEM.md (komplette Video-Pipeline-Doku)

Kein Code. Nur Markdown.
