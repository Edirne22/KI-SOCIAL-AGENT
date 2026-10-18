# OpenMontage: Private Medien einem Filmauftrag zuordnen

**Status:** Technischer Betreiberablauf. Noch keine fertige Telegram-Oberfläche
für die Szenenauswahl. Kein automatisches Social-Media-Posting.

## Voraussetzungen

- Privates Telegram-Album wurde mit `/privat` autorisiert und gespeichert.
- Die zurückgemeldete `tgalbum...`-ID bezeichnet das Album.
- Ein privater OpenMontage-Auftrag `tg-<update_id>` wurde bereits angelegt.
- Der Betreiber hat die zu verwendenden `asset_id`-Werte aus dem privaten
  R2-Manifest ermittelt und die Medienrechte für **jede** Szene ausdrücklich geprüft.
- R2-Credentials und `TELEGRAM_CHAT_ID` liegen ausschließlich in geschützter
  Ausführungsumgebung, nicht in öffentlichen Dateien oder Telegram-Nachrichten.

## Szenenauswahl

Beispiel `selections.json` (nicht ins öffentliche Repository committen):

```json
[
  {
    "scene_number": 1,
    "asset_id": "file00000001",
    "media_license": "owned_content",
    "rights_verified": true
  }
]
```

Die `asset_id` muss tatsächlich zum privaten Album gehören. `rights_verified`
darf nur nach ausdrücklicher Bestätigung gesetzt werden.

## Auswahl privat speichern

```bash
python -m scripts.openmontage_album_selection_cli \
  --request-id tg-42 \
  --album-job-id tgalbumaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --selections selections.json
```

Die Auswahl wird unveränderlich unter
`openmontage/album-selections/tg-42.json` in R2 gespeichert.
Der nachfolgende Produktionslauf lädt diese Datei und prüft Auftrag,
Album-ID und Telegram-Eigentümer.

## Produktion

Der bereits vorhandene Telegram-Befehl
`/montage album <tgalbum-ID> <Auftrag>` startet die GitHub-Action
mit der Album-ID. **Wichtig:** Die Auswahl muss vorher für die vom Befehl
neu erzeugte Request-ID existieren. Die automatische Zuordnung in einem
einzigen Telegram-Schritt ist noch offen. Deshalb ist der Befehl allein
noch keine vollständig benutzbare Medienproduktionsoberfläche.

Es gibt weder eine automatische Rechtefreigabe noch eine automatische
Facebook-/Instagram-Veröffentlichung.
