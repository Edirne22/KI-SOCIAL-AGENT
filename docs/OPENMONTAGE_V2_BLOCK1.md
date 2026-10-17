# OpenMontage V2 – Block 1

## Scope und Abnahmematrix

Isolierter FFmpeg-Renderer unter `integrations/openmontage/creative_renderer.py`.
Bestehende OpenMontage-Demo, Remotion-Rennkalender, Telegram, R2 und Publisher
bleiben unverändert. Kein Cloudflare-Container, VPS, Provider oder privates Medium.

| Kriterium | Nachweis |
| --- | --- |
| Vier synthetische Szenen, bewegte Titel, Zoom/Schwenk | echter Render und Bildstichproben |
| Drei Übergänge, korrekte Überlappung | fade / wipeleft / circleopen bei 3,4 / 6,8 / 10,2 s |
| Gültige MP4, Dauer, Auflösung, Frames, Audio | ffprobe-Vertrag plus vollständiger FFmpeg-Decode |
| Falsche Auflösung/Codec/Framezahl/NaN/Zusatzstream | negative Vertragstests |
| Prozessfehler/Timeout | keine finale MP4 und kein Erfolgsbericht |
| Wiederanlauf / paralleles gleiches Ziel | existierendes Verzeichnis/Symlink wird abgewiesen; neuer Lauf braucht neues Ziel |
| Keine vererbten Zugangsdaten | subprocess-Umgebung per Allowlist; kein shell=True |
| Bestehende Schnittstellen | OpenMontage-/R2-/Telegram-Regressionen ohne externe Aufrufe |
| CI / manuell startbarer Render | `openmontage-creative.yml`, PR und workflow_dispatch |
| Live-R2/Telegram/Publisher | N/A in Block 1: keine Änderung oder externe Übertragung |
| Private Medien / freie Aufträge | N/A: separater Block 2, keine behauptete Produktionsabnahme |

## Reproduzieren

Benötigt Python 3.10+, FFmpeg mit libx264/drawtext/xfade, ffprobe und
`/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (Ubuntu fonts-dejavu-core).
Keine Python-Drittanbieterpakete für den Renderer.

```bash
python integrations/openmontage/creative_renderer.py --output /tmp/om-v2-neuer-lauf
OPENMONTAGE_RENDER_E2E=1 python -m unittest discover -s tests -p test_openmontage_creative.py -v
```

Das Zielverzeichnis darf noch nicht existieren. Erzeugt werden erst nach
Medienprüfung `creative-demo.mp4`, `report.json` und `ffprobe.json`.
Nach Abbruch neues Ziel wählen; keine automatische Wiederverwendung alter Ergebnisse.
Die Bildmotive und der 100-BPM-Synthesizerklang werden deterministisch lokal erzeugt.
Binäridentische MP4s über verschiedene FFmpeg-/Encoder-Versionen sind nicht zugesagt.

## Tatsächlicher lokaler Rendernachweis

FFmpeg 6.1.1, vier geometrische PPM-Motive, H.264/yuv420p, AAC stereo,
720 × 1280, 30 fps, 426 Frames, 14,2 Sekunden, 1.637.427 Bytes.
Render inklusive Synthese und Validierung: **9,662 Sekunden**.
SHA-256: `fe55d56bd1f0fbf33514f15ae67a2ea8fd401354657a449e34e36d1804f0d41c`.
Vollständiger Decode erfolgreich. Bildstichproben bei den Szenen/Übergängen geprüft.
7 neue Tests inklusive echtem Zweitrender bestanden; 29 bestehende OpenMontage-
Vertragstests bestanden. CI-Nachweise stehen im PR; ein gestarteter Run ist kein PASS.

## GitHub Actions / Download

Workflow **OpenMontage V2 Creative Render**. PR-Läufe rendern tatsächlich, ohne Secrets.
Nach erfolgreichem Lauf enthält das Artefakt `openmontage-v2-synthetic-<sha>` ausschließlich
MP4 und zwei Prüfberichte (7 Tage Aufbewahrung). Kein R2- oder Social-Upload.
`workflow_dispatch` ist vorbereitet; eine neue Workflow-Datei wird auf GitHub erst nach
Aufnahme auf dem Default-Branch regulär manuell angeboten. Vor Merge daher PR-Render
verwenden; ein manueller Lauf darf nicht ohne Run-Beleg behauptet werden.

## Block 2 – offen

- Validierter Szenen-/Auftragsvertrag für frei wählbare Titel, Medien und Schnittlängen.
- Rhythmus-/Musikdramaturgie und weitere kreative Vorlagen statt fester Testszene.
- Autorisierter privater Medien-Intake außerhalb öffentlicher Actions-Artefakte.
- Neuen Renderer an bestehende Telegram-Aufträge und private R2-Vorschau anschließen.
- Echten Befehl → Renderer → privates R2 → Telegram-Nachweis gesondert abnehmen.
- Keine automatische Veröffentlichung; Merge dieses PR nur nach Bülents Freigabe.
