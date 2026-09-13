# Apify als Hauptquelle für Inspiration

## Reihenfolge

Der Inspiration-Agent verwendet für öffentliche Social-Posts:

1. **Apify** für Instagram und Facebook
2. **YouTube-Apify-Adapter** für YouTube
3. **Bright Data** nur, wenn Apify für Instagram, Facebook oder YouTube keine verwertbaren Datensätze liefert
4. Bright Data bleibt vorerst direkte Quelle für TikTok und X, bis dafür ein kontrollierter Apify-Adapter eingerichtet ist

Es werden höchstens zehn Beiträge pro Instagram- und Facebook-Lauf verarbeitet. Für Facebook wird dieses Limit direkt an den Apify-Actor übergeben; es begrenzt damit den Abruf, nicht nur den fertigen Report.

## Konfiguration

Erforderlich:

- GitHub Secret `APIFY_API_TOKEN`

Optional:

- `APIFY_INPUT_INSTAGRAM`
- `APIFY_INPUT_FACEBOOK`

Beide optionalen Werte sind JSON-Listen mit öffentlichen Profil-/Seiten-URLs, zum Beispiel:

```json
[{"url": "https://www.instagram.com/motogp/"}]
```

```json
[{"url": "https://www.facebook.com/MotoGP"}]
```

Wenn die optionalen Apify-Inputs fehlen, verwendet der Agent automatisch die bereits vorhandenen öffentlichen URLs aus `BRIGHTDATA_INPUT_INSTAGRAM` bzw. `BRIGHTDATA_INPUT_FACEBOOK`. Das Bright-Data-Token wird dafür nicht benötigt.

## Kontrolle und Kosten

- Jeder Lauf schreibt `memory/INSPIRATION_APIFY.md`.
- Technische Metadaten stehen in `memory/INSPIRATION_APIFY_DEBUG.md`.
- Tokens, Header und Rohantworten werden nicht geloggt.
- Der Telegram-Abschluss weist darauf hin, dass Apify als Hauptquelle verwendet wurde.
- Vor jedem Ausbau mit weiteren Plattformen zuerst die Apify-Abrechnung und das Nutzungsvolumen im Apify-Dashboard prüfen.\n- Im Apify-Dashboard ein persönliches monatliches Usage-Limit (empfohlen zum Start: 2–3 €) setzen. Ohne ausdrückliche Erhöhung darf kein Mehrverbrauch entstehen.
