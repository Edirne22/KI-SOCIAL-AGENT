# Sicherheitsregeln

## Grundprinzip
- Sicherheit geht vor Automatisierung.
- Jede automatisierte Aktion muss nachvollziehbar und kontrollierbar sein.
- Der Agent arbeitet nur mit offiziellen Schnittstellen und erlaubten Methoden.
- Es werden niemals Passwörter oder private Zugangsdaten in Dateien gespeichert.

## Freigabeprozess
- Vor jeder Veröffentlichung muss eine Freigabe durch Bülent erfolgen.
- Ausnahme: vorher festgelegte, ungefährliche Standard-Inhalte nach klaren Regeln.
- Freigaben erfolgen über das Handy oder eine definierte Schnittstelle.

## Datenschutz
- Keine privaten Daten anderer Personen verarbeiten oder teilen.
- Keine privaten Chats, GPS-Daten oder nicht-öffentlichen Informationen auslesen.
- Keine automatische Überwachung fremder Accounts.
- Öffentliche Daten (z. B. Play-Store-Bewertungen) nur für Analysezwecke verwenden.

## Plattform-Regeln
- Keine Bots, gekauften Follower, Likes oder künstliche Interaktionen.
- Kein Spam oder massenhaft unerwünschte Nachrichten.
- Keine Umgehung von Sicherheitsmechanismen oder Login-Automatisierung.

## API & Secrets
- API-Keys werden ausschließlich als GitHub Secrets gespeichert.
- Zugriffsrechte werden minimal gehalten (Least Privilege).
- Offizielle APIs und OAuth bevorzugen.

## Automatisierung
- Automatisch erlaubt: Content-Recherche, Ideen-Erstellung, Statistikanalyse, Content-Planung.
- Vor Veröffentlichung kontrollieren: alles, was veröffentlicht oder versendet wird.
- Niemals automatisch: private Daten, Spam, Übernahme fremder Accounts.

## Notfall
- Bei Fehlern oder verdächtigen Aktivitäten: Automatisierung pausieren.
- Bülent entscheidet über das weitere Vorgehen.

## Telegram-Freigabe

- Der Telegram-Bot dient nur zur persönlichen Freigabe durch Bülent.
- `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` werden ausschließlich als GitHub Secrets gespeichert.
- Telegram-Freigaben werden nur akzeptiert, wenn die Nachricht aus der hinterlegten `TELEGRAM_CHAT_ID` stammt.
- Eine Freigabe trägt Inhalte mit dem Status `FREIGEGEBEN` in `content/PUBLISHED.md` ein.
- Der Telegram-Bot veröffentlicht niemals selbst auf sozialen Plattformen und startet keine Publisher-Aktion.
- Bei fehlenden Secrets, ungültigen Antworten oder unbekannten Chats wird nichts freigegeben.

## Deal-Hunter

- Ausschließlich öffentliche Recherche und öffentlich bekannte Rabattcodes.
- Kein automatischer Kauf, keine Bestellung und keine Anmeldung ohne ausdrückliche Erlaubnis.
- Keine Zahlungsdaten speichern oder eingeben.
- Keine Umgehung von Captchas, Bot-Schutz, Shop-Sperren oder technischen Schutzmaßnahmen.
- Coupon-Tests erfordern eine Händler-Allowlist und ein dauerhaft gespeichertes Rate-Limit.
- Bei fehlender Quelle, Shop-Sperre oder Unsicherheit: überspringen und Bülent informieren.

## Preis-Tracking

- Nur öffentliche Recherche, kein automatischer Kauf und keine Anmeldung.
- Maximal 15 aktive Beobachtungen.
- Telegram-Nachrichten nur bei Preisänderungen; unsichere Preise sind als nicht bestätigt markiert.
- `stop` und `erledigt` beenden eine Beobachtung sofort.
- Der Auto-Track-Zustand wird ausschließlich in `memory/USER_PREFERENCES.md` gespeichert und kann jederzeit mit `auto-track: on` oder `auto-track: off` geändert werden.

## Inspiration Agent
- Nur öffentliche Daten, keine Logins oder privaten Profile.
- Quellen verlinken, Inhalte nicht kopieren und maximal zehn Anfragen je Anbieter/Plattform/Lauf.
- Bei Ausfall eines Anbieters laufen andere Adapter unabhängig weiter.

## Race Calendar
- Nur öffentliche Kalenderquellen nutzen und Zeiten als prüfpflichtig markieren, wenn sie nicht bestätigt sind.
- Poster bleiben Entwürfe; Veröffentlichung erst nach ausdrücklichem Telegram-Befehl `go`.

## Viral-Learning
- Nur öffentliche Daten und eigene Performance analysieren.
- Muster erkennen, keine fremden Posts kopieren; keine gekauften oder künstlichen Interaktionen.

## Growth-Hacker-Methodik
- Nur ehrliche, nachvollziehbare Metriken; fehlende Werte werden nicht geschätzt.
- Keine gekauften Follower, Likes oder künstlichen Interaktionen.
- Kein Clickbait ohne inhaltliche Einlösung.
- A/B-Tests starten nur nach Bülents ausdrücklicher Freigabe.
- Wettbewerber-Analyse verwendet ausschließlich öffentliche Daten und kopiert keine Inhalte.

## Qualitäts-Agent

- Der Qualitäts-Agent prüft und berichtet ausschließlich; er veröffentlicht nichts und startet keine Workflows neu.
- Er darf keine Inhalte, Freigaben, Watchlists oder Memory-Daten automatisch verändern.
- Telegram-Nachrichten gehen ausschließlich an die hinterlegte `TELEGRAM_CHAT_ID`.
- Qualitätsberichte enthalten keine Tokens, Cookies, Header, vollständigen Rohdaten oder privaten Informationen.
- Kritische Befunde werden klar dokumentiert und brauchen Bülents Entscheidung, bevor eine Reparatur erfolgt.
