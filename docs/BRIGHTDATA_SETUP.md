# Bright Data Setup

## Zweck

Bright Data liefert öffentliche Social-Media-Daten für den Inspiration Agent. Bright Data bietet je nach Produkt und Tarif einen kostenlosen Einstieg. Den aktuellen Umfang und monatliche Freikontingente bitte im eigenen Bright-Data-Dashboard prüfen.

## 1. Account und Datasets

1. Öffne [Bright Data](https://brightdata.com) und melde dich an.
2. Öffne im Dashboard **Web Scraper** → **Datasets**.
3. Wähle für Instagram, Facebook und YouTube jeweils ein passendes Dataset.
4. Kopiere pro Dataset die Dataset-ID (beginnt mit gd_) sowie das vom Dashboard gezeigte Input-JSON.

Die Dataset-ID allein reicht nicht: Jedes Dataset erwartet ein eigenes JSON-Input-Format.

## 2. GitHub konfigurieren

Unter **Settings → Secrets and variables → Actions**:

### Variables

- BRIGHTDATA_DATASET_INSTAGRAM
- BRIGHTDATA_DATASET_FACEBOOK
- BRIGHTDATA_DATASET_YOUTUBE
- BRIGHTDATA_ZONE – Name einer vorhandenen Unlocker-/SERP-Zone
- BRIGHTDATA_ENABLE_UNLOCKER_FALLBACK – standardmäßig false

### Secrets

- BRIGHTDATA_API_TOKEN
- BRIGHTDATA_INPUT_INSTAGRAM
- BRIGHTDATA_INPUT_FACEBOOK
- BRIGHTDATA_INPUT_YOUTUBE

Die Input-Secrets müssen gültiges JSON enthalten und werden unverändert an Bright Data gesendet. Beispiele:

    [{"url":"https://www.instagram.com/explore/tags/motogp/"}]

    [{"url":"https://www.facebook.com/MotoGP"}]

    [{"keyword":"Toprak Razgatlioglu","num_of_posts":10}]

Das korrekte Format stammt immer aus dem Input-Beispiel des tatsächlich ausgewählten Datasets.

## 3. Test und Diagnose

Starte **Actions → Inspiration Agent → Run workflow**. Prüfe danach:

- memory/BRIGHTDATA_DEBUG.md für Endpunkt, HTTP-Status, Snapshot-Status, Records und Error-Codes;
- memory/INSPIRATION_BRIGHTDATA.md für die Diagnose je Plattform;
- memory/INSPIRATION_IDEAS.md für die daraus abgeleiteten, belegten Ideen.

0 Datensätze ist nur dann ein normales leeres Ergebnis, wenn keine Error-Codes vorliegen. Bei dead_page zuerst Input-URL und Input-Format prüfen; falls beides korrekt ist, Dataset-ID und Dataset-Status im Bright-Data-Dashboard prüfen.

## Web Unlocker

Der Web Unlocker ist standardmäßig deaktiviert. Setze BRIGHTDATA_ENABLE_UNLOCKER_FALLBACK nur bewusst auf true. Pro Workflow-Lauf wird dann maximal eine Testanfrage ausgeführt; ohne BRIGHTDATA_ZONE wird sie übersprungen.
