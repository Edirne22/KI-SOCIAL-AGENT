# Apify-Suche für Deal-Hunter

## Zweck

Deal-Hunter nutzt zuerst öffentliche Google-Suchergebnisse über Apify. Es gibt keine Anmeldung bei Händlern, keinen Warenkorb und keinen Kauf.

## Kosten- und Sicherheitsgrenzen

- Actor: `datascraperes/google-serp-scraper`
- Land/Sprache: Deutschland / Deutsch
- Genau eine Ergebnisseite und höchstens zehn Treffer
- Hartes Kostenlimit: maximal **0,01 USD pro Suche**
- Der bestehende Secret `APIFY_API_TOKEN` wird verwendet; kein neuer Schlüssel nötig.

## Ergebnis

Telegram zeigt direkte HTTPS-Links. Sie sind antippbar und führen auf die jeweilige öffentliche Händler- oder Informationsseite. Preisangaben aus Suchtreffern werden als **nicht bestätigt** gespeichert und müssen vor einem Kauf im Shop geprüft werden.

## Fallback-Kette

1. Apify Google-Suche
2. SearXNG, falls eingerichtet
3. Gemini Search Grounding
4. Gemini-Wissenshinweis ohne aktuelle Preise

Wenn kein Live-Anbieter erreichbar ist, wird kein Preis erfunden oder gespeichert.
