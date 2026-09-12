# Asset-Struktur

## Ordner

| Typ | Pfad | Beispiel |
|---|---|---|
| Generierte Bilder | `assets/images/YYYY-MM/` | `2026-09-12-toprak-01.jpg` |
| Generierte Videos | `assets/videos/YYYY-MM/` | `2026-09-12-reel.mp4` |
| Karussells | `assets/carousels/YYYY-MM-DD-slug/` | `slide-1.jpg` |
| Rennposter | `assets/race-posters/` | `2026-W37-motogp.jpg` |
| Eigene Dateien | `assets/user-assets/` | `toprak.jpg` |
| Bereits veröffentlichte Alt-Assets | `assets/published/YYYY-MM/` | `2026-09-12-instagram-post-01.jpg` |
| Tests | `assets/test/` | nur temporär |

## Dateinamen

Format: `YYYY-MM-DD-<thema-slug>-NN.ext`.

Der Slug nutzt Kleinbuchstaben und Bindestriche. Deutsche und türkische Zeichen werden sauber normalisiert, etwa: „Öncü-Brüder in Istanbul“ → `oncu-brueder-in-istanbul`.

## Kompatibilität

In `PUBLISHED.md` sind neue vollständige Pfade empfohlen:

```markdown
Bild: assets/images/2026-09/2026-09-12-toprak-in-misano-01.jpg
```

Alte reine Dateinamen bleiben kompatibel. Sie werden ausschließlich bei genau einem Treffer aufgelöst; bei keinem oder mehreren Treffern bricht der Publisher mit einer klaren Meldung ab.

## Phase 1

Nach der Veröffentlichung werden Dateien **nicht** verschoben. Automatische Archivierung und Löschung sind ausdrücklich nicht Teil von Phase 1.

Cron-Ausdrücke in GitHub Actions laufen in UTC. Die Kommentare in den Workflows beziehen sich auf die deutsche Sommerzeit.

## Ausblick

Regelmäßige Videos sollten später in einen externen Asset-Speicher wie Cloudflare R2 oder Cloudinary ausgelagert werden, damit das Git-Repository klein bleibt.
