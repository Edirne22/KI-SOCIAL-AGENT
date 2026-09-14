# Musik-Agent

## So nutzt du automatische Musik

Der Musik-Agent verarbeitet nur **Reels** und **Stories** mit allen drei Angaben:

```text
Status: FREIGEGEBEN
Video: assets/eigenes-material/videos/dein-video.mp4
Musik: auto
```

Er wählt einen Track aus der lokalen Bibliothek, mischt ihn mit geringer Lautstärke in
das Video und ersetzt danach den Video-Pfad. Erst dann darf der normale Publisher
veröffentlichen. Solange `Musik: auto` dort steht, wartet der Publisher.

## Auswahl

| Inhalt | Kategorie |
| --- | --- |
| Rennen, MotoGP, Toprak, Yamaha usw. | `racing` |
| Tour, Ausfahrt, Reise, Türkei | `travel` |
| Community, ruhige oder allgemeine Beiträge | `chill` |

## Eigene Musik ergänzen

1. Datei in einen passenden Unterordner von `assets/musik/` hochladen.
2. In `config/MUSIC_LIBRARY.json` einen Eintrag mit Titel, Kategorie, Pfad und Lizenz ergänzen.
3. Nur eigene oder eindeutig erlaubte Musik in das öffentliche Repository hochladen.

## Startbibliothek

Die Einrichtung erfolgt einmalig über **Actions → Musikbibliothek einrichten → Run workflow**.
Die drei Starttracks stammen aus dokumentierten Public-Domain-/CC0-Quellen auf Wikimedia Commons.
