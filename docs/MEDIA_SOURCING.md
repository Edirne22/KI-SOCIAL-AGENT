# Medien schnell verwenden

## Grundidee

Der Beitragstext wird niemals nach Fahrernamen, Teams oder Rennbegriffen gesperrt. 
Entscheidend ist nur, wo das tatsächlich verwendete Bild oder Video abgelegt wurde.

## Einfacher Ablauf

1. Bild oder Video selbst in GitHub hochladen.
2. Eine der beiden Ordnerarten wählen:
   - Eigenes Material: `assets/eigenes-material/datei.jpg`
   - Einmalig bestätigte Quelle: `assets/freigegeben/motoetkinlikcom/datei.jpg`
3. Im Beitrag nur den Pfad eintragen:

```text
Bild: assets/freigegeben/motoetkinlikcom/misano-01.jpg
```

Keine zusätzliche Zeile für `Medienstatus`, `Nutzungsrecht` oder `Quelle` nötig.

## Einmalig freigegebene Quelle

Die erlaubten Quellen liegen in `config/TRUSTED_MEDIA_SOURCES.json`. 
Für eine weitere Quelle wird dort einmal ein Eintrag ergänzt, nachdem Bülent 
die Erlaubnis bestätigt hat. Danach gelten alle Medien im passenden Quellenordner automatisch als vorgeprüft.

## Reale Rennaufnahmen

`Bild: auto` oder `Video: auto` erzeugt keine KI-Rennaufnahme mit realen Fahrern. 
Das verhindert falsche Motorräder, Farben oder Fahrer. Für Toprak, MotoGP und 
andere Renn-News einfach ein echtes hochgeladenes Medium aus einem der obigen 
Ordner verwenden.

## Was bleibt unverändert

- Telegram-Freigabe entscheidet weiterhin, ob ein Beitrag veröffentlicht werden darf.
- Der Agent lädt keine fremden Medien selbst herunter.
- Ein unbekannter Medienpfad wird klar blockiert; der Beitragstext selbst nie.