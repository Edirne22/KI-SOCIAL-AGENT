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
