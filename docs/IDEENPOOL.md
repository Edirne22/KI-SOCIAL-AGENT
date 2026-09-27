# Ideenpool

## Social-/Realtime-Discovery – später prüfen

Status: **Ideenpool, nicht Teil von PR #163.** Erst angehen, wenn die Kernpipeline über längere Zeit stabil autonom läuft.

- Instagram: offizielle/zulässige Schnittstellen bevorzugen; externe Scraper-Dienste (z. B. Apify/RapidAPI) nur später gegen Kosten, Zuverlässigkeit und Datenschutz prüfen. Keine Abhängigkeit der Kernpipeline von Instagram.
- Telegram: mögliche türkische Racing-News-/Fan-Kanäle als zusätzliche Discovery-Quelle evaluieren; Rate-/Flood-Limits berücksichtigen.
- X/Twitter: RSSHub/Nitter-ähnliche Feeds nur als optionale Discovery-Schicht evaluieren, nicht als Primär-Faktenquelle.
- Structured Data / Live Timing: MotoGP-/WorldSBK-Ergebnis- und Timing-Daten auf belastbare strukturierte Feeds/APIs prüfen; experimentelle/undokumentierte Endpunkte nur als Adapter, nicht als Single Point of Failure.
- RSS-first: verfügbare Racing-RSS-Feeds vor HTML-Crawling nutzen, um Last und Fehleranfälligkeit zu reduzieren.
- Event-Klassifizierung: CRITICAL / RESULT / SESSION / CAREER / DISCOVERY / GENERAL als spätere Priorisierungs- und Alert-Schicht.
- Racer Registry ausbauen: Startnummer, aktuelle Serie/Team, Historie, Aliase, Quellenbeleg und verified_at; aktuelle Fakten nicht ungeprüft aus Social Posts übernehmen.
- Nach Stabilisierung 1–2 Wochen Produktionsdaten sammeln und danach gezielt entscheiden, welche dieser Erweiterungen echten Mehrwert liefern.
