from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram_bot import send_message

CONFIG_PATH = ROOT / "config" / "strecken.json"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
STORM_WIND_MS = 13.9


def _load_routes() -> list[dict]:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    routes = data.get("strecken", [])
    return routes if isinstance(routes, list) else []


def _fetch_weather(route: dict, api_key: str) -> dict:
    response = requests.get(
        OPENWEATHER_URL,
        params={
            "lat": route["lat"],
            "lon": route["lon"],
            "appid": api_key,
            "units": "metric",
            "lang": "de",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _condition_label(weather: dict) -> tuple[str, bool]:
    weather_items = weather.get("weather") or []
    first = weather_items[0] if weather_items else {}
    main = str(first.get("main", "")).lower()
    description = str(first.get("description", "")).strip() or "Wetter unbekannt"
    wind_speed = float((weather.get("wind") or {}).get("speed") or 0)

    not_recommended = (
        main in {"rain", "drizzle", "snow", "thunderstorm"}
        or wind_speed >= STORM_WIND_MS
    )
    return description, not_recommended


def _format_route_line(route: dict, weather: dict) -> str:
    temp = round(float((weather.get("main") or {}).get("temp", 0)))
    description, not_recommended = _condition_label(weather)
    if not_recommended:
        return f"⚠️ {route['name']}: {temp}°C, {description}, eher nicht"
    return f"✅ {route['name']}: {temp}°C, {description}, gute Bedingungen"


def main() -> int:
    try:
        routes = _load_routes()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"[weather-agent] Strecken-Konfiguration ungültig: {exc}")
        return 0

    if not routes:
        send_message("🏍️ Strecken-Check: Keine Strecken konfiguriert.")
        return 0

    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        print("[weather-agent] OPENWEATHER_API_KEY fehlt.")
        return 0

    lines = [
        f"🏍️ Strecken-Check für heute ({datetime.now().strftime('%d.%m.%Y')})"
    ]

    for route in routes:
        try:
            weather = _fetch_weather(route, api_key)
            lines.append(_format_route_line(route, weather))
        except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
            name = route.get("name", "Unbekannte Strecke")
            lines.append(f"⚠️ {name}: Wetterdaten nicht verfügbar")
            print(f"[weather-agent] {name}: {exc}")

    send_message("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
