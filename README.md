# KI-SOCIAL-AGENT
Persönlicher Cloud-KI-Agent für Social Media &amp; mehr

## Telegram-Bot einrichten

Der Telegram-Bot dient ausschließlich zur persönlichen Content-Freigabe durch Bülent. Er veröffentlicht selbst nichts auf Instagram, Facebook, TikTok oder einer anderen Plattform.

1. Öffne Telegram und schreibe `@BotFather`.
2. Sende `/newbot`, vergib einen Namen und einen eindeutigen Benutzernamen für den Bot.
3. Kopiere den von BotFather erzeugten Token. Teile ihn nie in Chats, Dateien oder Screenshots.
4. Schreibe dem neuen Bot einmal eine Nachricht, zum Beispiel `Hallo`.
5. Rufe lokal die Bot-API `getUpdates` mit deinem Token auf und suche in der Antwort nach `"chat":{"id": ...}`. Diese Zahl ist deine `TELEGRAM_CHAT_ID`.
6. Öffne im GitHub-Repository **Settings → Secrets and variables → Actions** und lege diese beiden Secrets an:
   - `TELEGRAM_BOT_TOKEN` – der Token von BotFather
   - `TELEGRAM_CHAT_ID` – ausschließlich Bülents persönlicher Chat
7. Starte anschließend **Telegram Morning Approval** manuell. Der Bot sendet drei Entwürfe; antworte mit `1,3`, `alle`/✅ oder `nein`/❌.

Der Morgen-Workflow speichert nur `memory/TELEGRAM_SESSION.md`. Der Empfangs-Workflow schreibt ausschließlich ausdrücklich freigegebene Entwürfe nach `content/PUBLISHED.md`. Eine Veröffentlichung bleibt immer ein separater, menschlich kontrollierter Schritt.

### Sicherheit

- Nutze den Bot nur im persönlichen Chat von Bülent, nicht in öffentlichen Gruppen.
- Teile Bot-Token und Chat-ID nicht; bei Verdacht auf Verlust den Token in BotFather sofort erneuern.
- Der Bot akzeptiert Freigaben nur aus der als Secret hinterlegten Chat-ID.
- Eine Telegram-Antwort ist eine Content-Freigabe, kein Auftrag zur automatischen Veröffentlichung.


## Inspiration- und Trend-Agenten

Optionale GitHub-Secrets für öffentliche Recherche:

- `APIFY_API_TOKEN` – Apify-Adapter
- `BRIGHTDATA_API_TOKEN` – Bright-Data-REST-Adapter
- `CRAWLBASE_TOKEN` – Crawlbase-Adapter

Für Bright Data können später zusätzlich `BRIGHTDATA_FACEBOOK_DATASET_ID` und `BRIGHTDATA_YOUTUBE_DATASET_ID` gesetzt werden. Tokens gehören ausschließlich in GitHub Secrets, niemals in Dateien.

Die Telegram-Kommandos `inspiration`, `race` und `viral` starten getrennte Arbeitsabläufe. `go` gibt ausschließlich einen vorhandenen Rennposter-Entwurf frei; keine dieser Aktionen veröffentlicht automatisch.
