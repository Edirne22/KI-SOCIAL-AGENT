# Bright Data: fünf Plattformen einrichten

## Zweck

Der Inspiration Agent nutzt die Bright-Data-Scraper-API für öffentliche Inhalte von Instagram, Facebook, YouTube, TikTok und X. Die aktuelle Preis- und Kontingent-Anzeige im eigenen Bright-Data-Dashboard ist maßgeblich.

## 1. Zugang im Bright-Data-Dashboard prüfen

1. Öffne das Bright-Data-Dashboard und wähle **Web Scraper / Scraper API**.
2. Prüfe für jede Plattform den dort gezeigten API-Beispielaufruf.
3. Die im Projekt hinterlegten Dataset-IDs und Endpoints dürfen nur verwendet werden, wenn sie mit deinem Dashboard-Beispiel übereinstimmen.
4. Facebook, YouTube, TikTok und Instagram dürfen nach einer HTTP-202-Antwort mit Snapshot-ID gepollt werden. Facebook und YouTube warten höchstens drei Minuten im Zehn-Sekunden-Takt; Instagram höchstens fünf Minuten im Zehn-Sekunden-Takt; TikTok höchstens fünf Minuten im 15-Sekunden-Takt. X wird direkt ausgewertet.

## 2. GitHub-Secrets

Öffne im Repository **Settings → Secrets and variables → Actions → Secrets** und hinterlege:

- `BRIGHTDATA_API_TOKEN`
- `BRIGHTDATA_INPUT_INSTAGRAM`
- `BRIGHTDATA_INPUT_FACEBOOK`
- `BRIGHTDATA_INPUT_YOUTUBE`
- `BRIGHTDATA_INPUT_TIKTOK`
- `BRIGHTDATA_INPUT_X`

Jedes Plattform-Secret enthält ausschließlich eine JSON-Liste. Der Agent ergänzt nur die dokumentierten Zeitraumfelder; für TikTok baut er aus dem Keyword eine Such-URL mit aktuellem Millisekunden-Zeitstempel.

### Instagram

```json
[
  {"url":"https://www.instagram.com/toprakrazgatlioglu/","num_of_posts":10,"post_type":"Post"},
  {"url":"https://www.instagram.com/motogp/","num_of_posts":10,"post_type":"Post"}
]
```

### Facebook

```json
[
  {"url":"https://www.facebook.com/MotoGP/","num_of_posts":10},
  {"url":"https://www.facebook.com/WorldSBK/","num_of_posts":10}
]
```

### YouTube

```json
[
  {"keyword":"MotoGP Toprak Razgatlioglu","num_of_posts":10,"include_shorts":true},
  {"keyword":"WorldSBK 2026 Highlights","num_of_posts":10,"include_shorts":true}
]
```

### TikTok

```json
[
  {"keyword":"motogp","num_of_posts":10},
  {"keyword":"toprak razgatlioglu","num_of_posts":10}
]
```

TikTok unterstützt in diesem Aufbau keinen Datumsfilter. Hat ein Treffer ein lesbares Datum, filtert der Agent lokal auf die letzten sieben vollen Kalendertage. Fehlt ein Datum, kennzeichnet der Report dies offen.

### X

```json
[
  {"url":"https://x.com/toprakrazgatlioglu"},
  {"url":"https://x.com/MotoGP"}
]
```

## 3. Zeitraum und Sicherheit

- Zeitbasis: Europe/Berlin.
- Zeitraum für Instagram, Facebook, YouTube und X: sieben abgeschlossene Kalendertage, von gestern bis sechs Tage davor.
- Fehlende Werte werden als „nicht verfügbar“ ausgewiesen; es werden keine Inhalte, Daten oder Kennzahlen erfunden.
- Der Agent akzeptiert kein altes SERP-Format mit `google_query`. Er meldet den Fehler klar, damit du das Secret ersetzen kannst.
- Tokens, Cookies und Header werden niemals in Logs geschrieben.

## 4. Test

1. Starte **Actions → Inspiration Agent → Run workflow**.
2. Prüfe `memory/BRIGHTDATA_DEBUG.md`: jede Plattform hat einen Status; Antworten sind auf 500 Zeichen und relevante Daten begrenzt.
3. Prüfe `memory/INSPIRATION_BRIGHTDATA.md`: Records und Quellenstatus je Plattform.
4. Prüfe `memory/INSPIRATION_IDEAS.md`: konkrete, belegte Themen und Ideen.

HTTP 400, 401, 403 und 404 werden nicht wiederholt. Bei 429, Timeout oder 5xx erfolgen höchstens drei Wiederholungen mit Wartezeiten. Facebook und YouTube pollen einen gültigen HTTP-202-Snapshot alle zehn Sekunden, höchstens drei Minuten. Instagram pollt bis fünf Minuten; TikTok bis fünf Minuten im 15-Sekunden-Takt. Bei einem Token- bzw. Rechtefehler gibt es höchstens eine Telegram-Meldung pro Tag.
