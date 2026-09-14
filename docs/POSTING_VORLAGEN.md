# Posting-Vorlagen

## Einfache Regel für Bilder und Videos

| Dein Material | Hochladen nach | Im Beitrag eintragen |
| --- | --- | --- |
| Eigenes Foto oder eigenes Video | `assets/eigenes-material/bilder/` oder `assets/eigenes-material/videos/` | bei Bildern den Pfad aus `bilder/`, bei Videos den Pfad aus `videos/` |
| Bild/Video einer einmalig bestätigten Quelle, z. B. @motoetkinlikcom | `assets/freigegeben/motoetkinlikcom/` | den vollständigen Pfad bei `Bild:` oder `Video:` |

Ein Screenshot oder Ausschnitt ist technisch ein normales Bild. Für die Veröffentlichung zählt im System ausschließlich der eingetragene Medienpfad. Es sind nie zusätzliche Zeilen wie `Quelle:`, `Nutzungsrecht:` oder `Medienstatus:` nötig.

## Vorlagen

| Ziel | Überschrift in `content/PUBLISHED.md` | Pflichtfelder | Medienfeld |
| --- | --- | --- | --- |
| Instagram-Post | `## Instagram` | `Status: FREIGEGEBEN`, `Text:` | `Bild: assets/...jpg` |
| Facebook-Post mit Bild | `## Facebook` | `Status: FREIGEGEBEN`, `Text:` | `Bild: assets/...jpg` |
| Facebook-Textpost | `## Facebook` | `Status: FREIGEGEBEN`, `Text:` | keines |
| Instagram-Reel | `## Instagram Reel` | `Status: FREIGEGEBEN`, `Text:` | `Video: assets/...mp4` |
| Instagram-Story | `## Story` | `Status: FREIGEGEBEN` | `Bild:` oder `Video:` |
| Instagram-Karussell | `## Instagram Karussell` | `Status: FREIGEGEBEN`, `Text:` | mindestens zwei Einträge unter `Bilder:` |
| Facebook-Karussell | `## Facebook Karussell` | `Status: FREIGEGEBEN`, `Text:` | mindestens zwei Einträge unter `Bilder:` |

> Für eine Story immer `## Story` verwenden, nicht `## Instagram Story`.

## Kopierbare Beispiele

### Instagram-Post

```text
## Instagram
Status: FREIGEGEBEN
Freigabe: Telegram
Text:
Dein Text hier.
Bild: assets/freigegeben/motoetkinlikcom/toprak-misano-01.jpg
```

### Facebook-Post mit Bild

```text
## Facebook
Status: FREIGEGEBEN
Freigabe: Telegram
Text:
Dein Facebook-Text hier.
Bild: assets/freigegeben/motoetkinlikcom/toprak-misano-01.jpg
```

### Instagram-Reel

```text
## Instagram Reel
Status: FREIGEGEBEN
Freigabe: Telegram
Text:
Deine Reel-Caption hier.
Video: assets/freigegeben/motoetkinlikcom/toprak-misano-01.mp4
```

### Instagram-Story

```text
## Story
Status: FREIGEGEBEN
Freigabe: Telegram
Bild: assets/eigenes-material/ausfahrt-01.jpg
```

### Instagram-Karussell

```text
## Instagram Karussell
Status: FREIGEGEBEN
Freigabe: Telegram
Text:
Deine Caption hier.
Bilder:
- assets/freigegeben/motoetkinlikcom/toprak-01.jpg
- assets/freigegeben/motoetkinlikcom/toprak-02.jpg
- assets/freigegeben/motoetkinlikcom/toprak-03.jpg
```

## Optional

- Für eigene Bilder: `assets/eigenes-material/bilder/…`; für eigene Videos: `assets/eigenes-material/videos/…`.
- `Quelle:`, `Nutzungsrecht:` und `Medienstatus:` sind vollständig optional und werden nicht als Veröffentlichungsbedingung verwendet.
- `Bild: auto` oder `Video: auto` wird niemals veröffentlicht, solange dort noch `auto` steht. Erst wenn die Medienerzeugung einen echten Pfad eingesetzt hat, ist der Block medienreif.
- Telegram-Freigabe bleibt immer erforderlich. Ohne `Status: FREIGEGEBEN` veröffentlicht kein Publisher etwas.