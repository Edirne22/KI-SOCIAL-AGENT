# OpenMontage über Telegram – einfache Bedienungsanleitung

> **Stand:** Vorbereitung. Die automatische Szenenauswahl und der
> vollständig bedienbare Telegram-Ablauf sind noch nicht fertig.
> Die folgenden Befehle sind kein Nachweis einer erfolgreichen Live-Produktion.

## Eigene Fotos und Videos privat speichern

Sende ein unterstütztes Foto oder Video an den autorisierten Telegram-Bot
und füge als Bild-/Videobeschriftung `/privat` hinzu. Der Bot speichert
das Material privat, sofern Dateityp, Downloadlimit und R2-Zugriff passen.
Für zusammengehörige Telegram-Alben die vom Bot zurückgegebene
`tgalbum...`-Kennung notieren.

**Wichtig:** Die Bot-Downloadgrenze beträgt derzeit etwa 19 MiB pro Datei.
Größere Dateien brauchen einen gesonderten Upload-Weg.

## Filmauftrag mit Album anfragen

```text
/montage album tgalbum<32 hexadezimale Zeichen> Erstelle einen dynamischen Geburtstagsfilm
```

Die echte Album-ID muss aus der Telegram-Rückmeldung stammen.
Der Befehl ist nur für den konfigurierten Eigentümer gedacht.

## Noch nicht automatisch

Die gewünschten Szenen und die Nutzungsrechte müssen derzeit separat
dem privaten Auftrag zugeordnet werden. Der Telegram-Befehl allein
übernimmt diese Zuordnung noch nicht. Ohne gültige Auswahl kann der
Produktionslauf nicht erfolgreich abschließen.

## Film prüfen und freigeben

Ein technisch erzeugtes MP4 bedeutet nicht, dass es bereits veröffentlicht
wurde. Redaktionelle Freigabe und Social-Media-Veröffentlichung sind
getrennte Schritte. Es erfolgt kein automatisches Facebook-/Instagram-Posting.

## Wenn etwas nicht funktioniert

- `/montage status` zeigt den zuletzt erreichbaren GitHub-Status.
- Bei `PRIVATE_MEDIA_UNAUTHORIZED` den autorisierten Chat prüfen.
- Bei `PRIVATE_MEDIA_INVALID` Album-ID, Auswahl und Rechte prüfen.
- Fehlende Medien niemals durch unbestätigte Fremdbilder ersetzen.

**Nächster Ausbauschritt:** Eine geführte Telegram-Szenenauswahl, damit
keine manuellen JSON-Dateien oder GitHub-Befehle mehr nötig sind.
