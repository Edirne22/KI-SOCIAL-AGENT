# Externe API-Referenz (public-apis)

Diese Übersicht enthält eine gefilterte Auswahl bekannter und zuverlässiger externer Datenquellen aus dem öffentlichen Repository `public-apis/public-apis` für die Agenten-Entwicklung mit 0-€-Fokus.

> **Abgrenzung:** Hier geht es um externe Datenquellen (Wetter, News, Sport, etc.), nicht um lokale Werkzeuge oder Medien-Tools (wie FFmpeg, Kinocut, etc.).

---

## Weather (Wetter)

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| Open-Meteo | Vorhersagen, Historien- & Wetterdaten weltweit ohne API-Key | Nein | ja (unbegrenzt) | Ja | Ja | [Open-Meteo](https://open-meteo.com/) |
| OpenWeatherMap | Globale Wetterdaten, Vorhersagen und historische Wetterdaten | `apiKey` | limitiert (1.000 Calls/Tag) | Ja | Ja | [OpenWeatherMap](https://openweathermap.org/api) |
| WeatherAPI | Aktuelle Wetterdaten, 14-Tage-Prognose und Geocoding | `apiKey` | limitiert (1.000.000 Calls/Monat) | Ja | Ja | [WeatherAPI](https://www.weatherapi.com/) |
| wttr.in | Konsolen- & HTTP-freundlicher Wetterdienst in Plain Text / JSON | Nein | ja (unbegrenzt) | Ja | Ja | [wttr.in](https://github.com/chubin/wttr.in) |

---

## Sports & Fitness

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| TheSportsDB | Sportdatenbank für Ligen, Teams, Spieler und Events | `apiKey` | limitiert (kostenloser Test-Key `1`) | Ja | Ja | [TheSportsDB](https://www.thesportsdb.com/free_sports_api) |
| Ergast F1 | Historische Ergebnisse und Daten der Formel 1 | Nein | ja (unbegrenzt) | Ja | Ja | [Ergast F1](http://ergast.com/mrd/) |
| Football-Data.org | Fußballdaten für europäische Ligen und Wettbewerbe | `apiKey` | limitiert (10 Calls/Min) | Ja | Ja | [Football-Data](https://www.football-data.org/) |
| Open Liga DB | Daten deutscher Fußball-Ligen (Bundesliga etc.) | Nein | ja (unbegrenzt) | Ja | Ja | [OpenLigaDB](https://www.openligadb.de/) |

---

## News (Nachrichten)

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| NewsAPI | Globale Schlagzeilen und Nachrichtenartikel durchsuchen | `apiKey` | limitiert (100 Calls/Tag, nur Dev) | Ja | Ja | [NewsAPI](https://newsapi.org/) |
| Currents API | Internationale News & Artikel in Echtzeit | `apiKey` | limitiert (600 Calls/Tag) | Ja | Ja | [Currents API](https://currentsapi.services/) |
| Hacker News API | Offizielle Firebase- & Algolia-API für Hacker News | Nein | ja (unbegrenzt) | Ja | Ja | [Hacker News API](https://github.com/HackerNews/API) |
| Spaceflight News API | Nachrichten und Artikel zu Raumfahrt & Astronomie | Nein | ja (unbegrenzt) | Ja | Ja | [Spaceflight News](https://spaceflightnewsapi.net/) |

---

## Video

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| YouTube Data API v3 | Videos, Kanäle und Playlists suchen und abrufen | `apiKey` | limitiert (10.000 Punkte/Tag) | Ja | Ja | [YouTube API](https://developers.google.com/youtube/v3) |
| Vimeo API | Videos suchen, Metadaten abrufen und verwalten | `OAuth2` | limitiert (Grundkontingent) | Ja | Ja | [Vimeo Developer](https://developer.vimeo.com/) |
| Pexels Video API | Kostenlose Stock-Videos suchen und herunterladen | `apiKey` | limitiert (200 Calls/Stunde) | Ja | Ja | [Pexels API](https://www.pexels.com/api/) |
| Pixabay API | Freie Videos und Bilder durchsuchen und abrufen | `apiKey` | limitiert (5.000 Calls/Stunde) | Ja | Ja | [Pixabay API](https://pixabay.com/api/docs/) |

---

## Social

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| Reddit API | Subreddits, Posts, Kommentare und User-Daten auslesen | `OAuth2` | limitiert (100 Calls/Min) | Ja | Ja | [Reddit API](https://www.reddit.com/dev/api/) |
| Mastodon API | Dezentrales Social-Network: Statuses, Profile & Timelines | `OAuth2` | ja (unbegrenzt / instanzabhängig) | Ja | Ja | [Mastodon Docs](https://docs.joinmastodon.org/api/) |
| Bluesky AT Protocol | Dezentrales Netz: Feed, Posts, Interaktionen lesen | `Bearer` / Nein | ja (unbegrenzt) | Ja | Ja | [Bluesky API](https://docs.bsky.app/) |
| Telegram Bot API | Bots erstellen, Nachrichten senden/empfangen & Updates | `apiKey` | ja (unbegrenzt / Ratenlimits) | Ja | Ja | [Telegram API](https://core.telegram.org/bots/api) |

---

## Vehicle (Fahrzeuge)

| Name | Beschreibung | Auth | Kostenloser Tier | HTTPS | CORS | Link |
| --- | --- | --- | --- | --- | --- | --- |
| NHTSA VPIC | Fahrzeug-Spezifikationen, VIN-Decoder & Herstellerdaten | Nein | ja (unbegrenzt) | Ja | Ja | [NHTSA VPIC](https://vpic.nhtsa.dot.gov/api/) |
| Tankerkönig API | Echtzeit-Kraftstoffpreise (Diesel, E5, E10) in Deutschland | `apiKey` | limitiert (Fair-Use) | Ja | Ja | [Tankerkönig](https://creativecommons.tankerkoenig.de/) |
| Open Charge Map | Globale Datenbank für Elektrofahrzeug-Ladestationen | `apiKey` | limitiert (Fair-Use) | Ja | Ja | [Open Charge Map](https://openchargemap.org/site/develop/api) |
| Bike Index API | Globale Fahrrad-Registrierungs- und Diebstahldatenbank | Nein | ja (unbegrenzt) | Ja | Ja | [Bike Index](https://bikeindex.org/documentation/api_v3) |
