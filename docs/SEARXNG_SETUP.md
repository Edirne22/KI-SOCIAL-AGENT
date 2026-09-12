# SearXNG einrichten

SearXNG ist eine selbst gehostete Meta-Suchmaschine. Der Deal-Hunter nutzt sie automatisch, sobald das GitHub-Secret `SEARXNG_URL` gesetzt ist. Ohne dieses Secret bleibt Gemini Search Grounding aktiv.

> Ein eigener SearXNG-Server reduziert die Abhängigkeit von Gemini, hebt aber Captchas oder Limits der einzelnen Suchmaschinen nicht automatisch auf.

## Voraussetzungen

- VPS mit Docker und Docker Compose
- HTTPS-geschützte Domain, die GitHub Actions erreichen kann
- Reverse Proxy und Zugriffsschutz, wenn die Instanz aus dem Internet erreichbar ist

Die offizielle SearXNG-Dokumentation empfiehlt die Bereitstellung über Docker Compose:

<https://docs.searxng.org/admin/installation-docker.html>

## Installation mit Docker Compose

Auf dem VPS:

```bash
mkdir -p ~/searxng/core-config
cd ~/searxng
curl -fsSL -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml
curl -fsSL -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
cp .env.example .env
docker compose up -d
```

Danach die Datei `core-config/settings.yml` anpassen. Die JSON-Suche muss aktiviert sein:

```yaml
search:
  formats:
    - html
    - json
```

Weitere Details zur Search-API:

<https://docs.searxng.org/dev/search_api.html>

## Sicherheit

- Ausschließlich HTTPS verwenden.
- SearXNG nicht ungeschützt öffentlich freigeben.
- Reverse Proxy, Zugriffsbeschränkung und Rate-Limits einrichten.
- Keine Zugangsdaten in dieses Repository schreiben.
- Die eigene Instanz muss für GitHub Actions erreichbar sein.

## GitHub-Secret setzen

Nach erfolgreichem Test im GitHub-Repository unter **Settings → Secrets and variables → Actions** anlegen:

```text
SEARXNG_URL=https://deine-domain.example
```

Der Wert darf nur die Basis-URL enthalten, ohne Suchbegriff und ohne Token.

## Test

```bash
curl "https://deine-domain.example/search?q=Motorradhandschuhe&format=json&categories=general"
```

Die Antwort muss JSON mit einem Feld `results` liefern. Danach den Workflow **Deal Hunter** manuell starten. Im Repository steht anschließend in `memory/SEARCH_PROVIDER_LOG.md` der verwendete Provider.
