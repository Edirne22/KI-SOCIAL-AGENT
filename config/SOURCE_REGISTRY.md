# Quellenregister

Dieses Register unterscheidet Faktenquellen von Medienrechten. Eine öffentliche
Quelle erlaubt **nicht** automatisch, ihr Foto oder Video erneut hochzuladen.

## Primärquellen

### MotoGP – offizielle Website und Accounts
- Faktenquelle: https://www.motogp.com/
- Vertrauensstufe: offiziell
- Einsatz: Ergebnisse, Termine, offizielle Meldungen und Links.
- Mediennutzung: Originalbilder und -videos nicht automatisch herunterladen oder
  erneut hochladen. Nur verlinken oder mit ausdrücklicher Nutzungsfreigabe.

### WorldSBK – offizielle Website und Accounts
- Faktenquelle: https://www.worldsbk.com/
- Vertrauensstufe: offiziell
- Einsatz: WorldSBK-Ergebnisse, Renntermine und Meldungen.
- Mediennutzung: nur verlinken oder mit ausdrücklicher Nutzungsfreigabe.

## Sekundärquellen

### Instagram @motoetkinlik
- Faktenquelle: öffentlicher Instagram-Account.
- Vertrauensstufe: sekundär; wichtige Fakten vor Veröffentlichung mit einer
  Primärquelle prüfen.
- Mediennutzung: Bülent hat eine persönliche Erlaubnis bestätigt. Hochgeladene
  Medien dieser Quelle werden über `assets/freigegeben/motoetkinlikcom/` und
  `config/TRUSTED_MEDIA_SOURCES.json` einmalig freigegeben.

### Knieschleifer aus Überzeugung (Community)
- **Instagram** (öffentlich)
  - Vertrauensstufe: sekundär; Fakten vor Veröffentlichung prüfen
  - Mediennutzung: nur verlinken, kein Re-Upload ohne schriftliche Freigabe

### Bike Society NRW (Community)
- **Instagram/WhatsApp** (öffentlich)
  - Vertrauensstufe: sekundär; Fakten vor Veröffentlichung prüfen
  - Mediennutzung: nur verlinken, kein Re-Upload ohne schriftliche Freigabe

## Erlaubte Medienarten
- EIGENES_MATERIAL: Bülents eigenes Foto oder Video.
- QUELLE_BESTÄTIGT: fremdes Material mit URL und bestätigtem Nutzungsrecht.
- LIZENZIERT: rechtmäßig erworbenes Stockmaterial mit Lizenznachweis.
- KI_GENERIERT: nur für neutrale Reise-, Landschafts-, Biker- oder
  Technikstimmung; nie als reale Aufnahme eines Fahrers, Teams oder Rennens.


## Vereinfachte Medienfreigabe

- Fahrernamen oder Rennbegriffe im Text sind nie ein Freigabekriterium.
- Eigenes Material unter `assets/eigenes-material/` ist ohne zusätzliche
  Metadaten verwendbar.
- Einmalig bestätigte Quellen werden unter `assets/freigegeben/<quelle>/`
  abgelegt; die Quelle muss in `TRUSTED_MEDIA_SOURCES.json` stehen.
