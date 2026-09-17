# Remotion Rennkalender-Video

Ein isoliertes Remotion-Projekt zur programmatischen Generierung von 7-Sekunden-Videos (1080x1920) für den Rennkalender mit viralen Social-Media-Animationen.

## Features & Animationen

- **Kinetic Typography**: Das Rennserien-Thema erscheint Wort-für-Wort mit Scale-Bounce Effect.
- **Glitch Effect**: RGB-Glitch-Split beim Übergang (Frames 45–50).
- **Bouncy TikTok-Style Captions**: Pop-In Effekte für Rennstrecke & Datum mit Spring-Physik.
- **Particle Rain**: Dezenter Partikel-Regen am Ende des Videos.
- **Line Overlay**: Animierte rote Akzentlinien in den ersten 2 Sekunden.
- **Dark Theme**: Dunkler Hintergrund, rote Akzentfarben, weiße Typografie.

## Lokale Entwicklung & Rendering

### Voraussetzung
Node.js >= 18 installed.

### Installation
```bash
cd remotion
npm install
```

### Preview-Studio starten
```bash
npm start
```

### Lokal rendern
```bash
npm run build
```
Oder direkt via Remotion CLI:
```bash
npx remotion render RaceCalendar out/video.mp4 --props='{"series":"MotoGP","track":"Red Bull Ring","dateRange":"18.–20. September 2026"}'
```

## GitHub Actions Workflow

Ein automatisierter Rendervorgang steht unter `.github/workflows/render-race-calendar.yml` bereit.

1. Gehe in GitHub zu **Actions** > **Render Race Calendar Video**.
2. Wähle **Run workflow**.
3. Gib `series`, `track` und `date_range` an.
4. Nach Abschluss des Workflows kann das gerenderte Video (`race-calendar-video.mp4`) unter **Artifacts** heruntergeladen werden.
