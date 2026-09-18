"""Aktualisiert memory/RACE_CALENDAR.json monatlich via Agnes (agnes-2.5-flash)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
import re
import time
from datetime import datetime

import requests
from PIL import Image

CALENDAR_FILE = Path("memory/RACE_CALENDAR.json")

AGNES_URL = "https://apihub.agnes-ai.com/v1/chat/completions"
AGNES_MODEL = "agnes-2.5-flash"
RETRY_DELAYS = [5, 15, 30]

BRAND_SOURCES = {
    "Ducati": {
        "racing_model": "Desmosedici GP",
        "racing_url":   "https://www.ducati.com/ww/en/racing/motogp",
        "street_model": "Panigale V4 R",
        "street_url":   "https://www.ducati.com/de/de/motorraeder/panigale/panigale-v4-r",
    },
    "Aprilia": {
        "racing_model": "RS-GP",
        "racing_url":   "https://www.aprilia.com/de_DE/racing/motogp/",
        "street_model": "RSV4 1100",
        "street_url":   "https://www.aprilia.com/de_DE/modelle/rsv4/rsv4-1100-4t-4v-2025/",
    },
    "KTM": {
        "racing_model": "RC16",
        "racing_url":   "https://www.ktm.com/de-de/racing/motogp.html",
        "street_model": "1290 Super Duke R",
        "street_url":   "https://www.ktm.com/de-de/models/naked-bikes/1290-super-duke-r.html",
    },
    "Honda": {
        "racing_model": "RC213V",
        "racing_url":   "https://www.honda.racing/motogp",
        "street_model": "CBR1000RR-R Fireblade SP",
        "street_url":   "https://powersports.honda.com/motorcycle/supersport/cbr1000rr-r-fireblade-sp/2026/cbr1000rr-r-fireblade-sp",
    },
    "Yamaha": {
        "racing_model": "YZR-M1",
        "racing_url":   "https://www.yamaha-racing.com/series/grand-prix/motogp/bike/",
        "street_model": "YZF-R1M",
        "street_url":   "https://r1m.yamaha-motor.eu",
    },
    "BMW": {
        "racing_model": "M1000RR",
        "racing_url":   "https://www.bmw-motorrad.de/de/models/m/m1000rr.html",
        "street_model": "M1000RR",
        "street_url":   "https://www.bmw-motorrad.de/de/models/m/m1000rr.html",
    },
}

MOTOGP_BRANDS = ["Ducati", "Aprilia", "KTM", "Honda", "Yamaha"]
WSBK_BRANDS = MOTOGP_BRANDS + ["BMW"]


def call_agnes_json(prompt: str, api_key: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AGNES_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            print(f"[race-update] Agnes API Aufruf (Versuch {attempt}/{len(RETRY_DELAYS)})...")
            response = requests.post(AGNES_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                return json.loads(content.strip())
            else:
                print(
                    f"[race-update] Agnes Versuch {attempt}/{len(RETRY_DELAYS)}: "
                    f"HTTP {response.status_code} ({response.text[:200]})"
                )
        except Exception as error:
            print(
                f"[race-update] Agnes Versuch {attempt}/{len(RETRY_DELAYS)} "
                f"Fehler: {type(error).__name__}: {error}"
            )

        if attempt < len(RETRY_DELAYS):
            print(f"[race-update] Warte {delay}s vor nächstem Versuch...")
            time.sleep(delay)

    return None


def try_og_image(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        m = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r.text, re.I)
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                r.text, re.I)
        return m.group(1) if m else None
    except Exception:
        return None


def search_openverse(query: str) -> str | None:
    """Openverse API – CC-lizenzierte Bilder, kein Key nötig."""
    try:
        url = "https://api.openverse.org/v1/images/"
        params = {
            "q": query,
            "page_size": 5,
            "license_type": "commercial,modification",
            "mature": "false",
        }
        r = requests.get(url, params=params, timeout=15,
                         headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"})
        if r.status_code != 200:
            return None
        for hit in r.json().get("results", []):
            if hit.get("width", 0) >= 1000 and hit.get("height", 0) >= 1000:
                return hit.get("url")
        return None
    except Exception:
        return None


def search_wikimedia(query: str) -> str | None:
    """Wikimedia Commons – mit Status-Check (Review-Korrektur 1)."""
    try:
        api = "https://commons.wikimedia.org/w/api.php"
        r = requests.get(api, timeout=10,
                         headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"},
                         params={
                             "action": "query",
                             "list": "search",
                             "srsearch": f"{query} filetype:bitmap",
                             "srnamespace": 6,
                             "srlimit": 5,
                             "format": "json",
                         })
        if r.status_code != 200:
            return None
        for hit in r.json().get("query", {}).get("search", []):
            r2 = requests.get(api, timeout=10,
                              headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"},
                              params={
                                  "action": "query",
                                  "titles": hit["title"],
                                  "prop": "imageinfo",
                                  "iiprop": "url|size",
                                  "format": "json",
                              })
            if r2.status_code != 200:
                continue
            for page in r2.json().get("query", {}).get("pages", {}).values():
                for info in page.get("imageinfo", []):
                    if info.get("width", 0) >= 1000 and info.get("height", 0) >= 1000:
                        return info["url"]
        return None
    except Exception:
        return None


def download_image(url: str, path: str) -> bool:
    try:
        r = requests.get(url, timeout=20, stream=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return False
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return os.path.getsize(path) > 10240
    except Exception:
        return False


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def normalize_bike_image(path: str) -> bool:
    try:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize((1080, 1080), Image.LANCZOS)
        img.save(path, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"[race-update] Bild-Normalisierung fehlgeschlagen: {e}")
        return False


def get_bike_image(brand: str, model: str, racing_url: str, street_url: str, date_str: str) -> tuple[str | None, str | None]:
    os.makedirs(f"assets/images/{date_str[:7]}", exist_ok=True)
    local_path = f"assets/images/{date_str[:7]}/{date_str}-bike-{slug(brand)}-{slug(model)}.jpg"

    # 1. Rennsport-og:image
    url = try_og_image(racing_url)
    if url and download_image(url, local_path):
        normalize_bike_image(local_path)
        return local_path, "og:racing"

    # 2. Straßen-og:image
    url = try_og_image(street_url)
    if url and download_image(url, local_path):
        normalize_bike_image(local_path)
        return local_path, "og:street"

    # 3. Openverse
    url = search_openverse(f"{brand} {model} motorcycle")
    if url and download_image(url, local_path):
        normalize_bike_image(local_path)
        return local_path, "openverse"

    # 4. Wikimedia
    url = search_wikimedia(f"{brand} {model}")
    if url and download_image(url, local_path):
        normalize_bike_image(local_path)
        return local_path, "wikimedia"

    # 5. Agnes-Editorial
    try:
        from generate_agnes_media import agnes_generate_image
        img_bytes = agnes_generate_image(
            prompt=(f"Editorial motorcycle photo of {brand} {model}, "
                    f"motorsport style, dramatic lighting, 1024x1024")
        )
        if img_bytes:
            with open(local_path, "wb") as f:
                f.write(img_bytes)
            if os.path.exists(local_path) and os.path.getsize(local_path) > 10240:
                normalize_bike_image(local_path)
                return local_path, "agnes"
    except Exception as e:
        print(f"[race-update] Agnes-Fallback fehlgeschlagen: {e}")

    return None, None


def fetch_bike_of_weekend(event: dict, key: str) -> dict | None:
    series = event.get("series", "").strip()
    if series in ("WorldSBK", "WSBK"):
        available_brands = WSBK_BRANDS
    else:
        available_brands = MOTOGP_BRANDS

    event_title = f"{series} {event.get('track', '')}".strip()
    prompt = f"""Wähle EINE Marke aus dieser festen Liste – keine Erfindungen:

{', '.join(available_brands)}

Begründe in 2–3 Sätzen, warum diese Marke zum Rennwochenende ({event_title}) passt.
Direkt, community-nah, deutsch, ohne Marketingsprache.

Antworte NUR mit JSON:
{{"brand": "KTM", "story": "..."}}"""

    bike_data = call_agnes_json(prompt, key)
    brand = None
    story = ""
    if isinstance(bike_data, dict):
        brand = bike_data.get("brand")
        story = str(bike_data.get("story", "")).strip()

    if not brand or brand not in BRAND_SOURCES:
        if brand:
            print(f"[race-update] Unbekannte Marke '{brand}' geliefert. Fallback auf Ducati.")
        else:
            print(f"[race-update] Keine Marke von Agnes geliefert. Fallback auf Ducati.")
        brand = "Ducati"

    brand_info = BRAND_SOURCES[brand]
    model = brand_info["street_model"]
    racing_url = brand_info["racing_url"]
    street_url = brand_info["street_url"]

    date_str = event.get("date_start", "")
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    image_local, image_source = get_bike_image(brand, model, racing_url, street_url, date_str)

    bike_result = {
        "brand": brand,
        "model": model,
        "category": "Rennsport oder Straße",
        "story": story,
        "source_url": street_url,
    }
    if image_local:
        bike_result["image_local"] = image_local
        bike_result["image_source"] = image_source

    return bike_result


def update_calendar() -> None:
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        print("[race-update] Warnung: AGNES_API_KEY fehlt - Kalender-Update nicht möglich.")
        sys.exit(0)

    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Heute ist {today_str}. Recherche die kommenden 4 Rennwochenenden von MotoGP, WorldSBK oder Formel 1.

Gib ausschließlich ein valides JSON-Objekt zurück, das exakt folgender Struktur entspricht:

{{
  "events": [
    {{
      "date_start": "YYYY-MM-DD",
      "date_end": "YYYY-MM-DD",
      "series": "MotoGP",
      "track": "Streckenname · Ort",
      "sessions": ["Fr: Freies Training", "Sa: Qualifying & Sprint", "So: Hauptrennen"],
      "source": "https://www.motogp.com/en/calendar"
    }}
  ]
}}

Regeln:
- date_start und date_end müssen im Format YYYY-MM-DD sein.
- series muss MotoGP, WorldSBK oder Formel 1 sein.
- track muss Name der Rennstrecke und Ort enthalten.
- source muss eine valide, offizielle URL sein.
- Falls du unsicher bist oder weniger Events findest, gib so viele fundierte kommende Events wie möglich an.
"""

    data = call_agnes_json(prompt, key)
    if not isinstance(data, dict) or "events" not in data or not isinstance(data["events"], list):
        print("[race-update] Warnung: Agnes-Recherche fehlgeschlagen. memory/RACE_CALENDAR.json bleibt unverändert.")
        sys.exit(0)

    # Validierung & Normalisierung
    valid_events = []
    for event in data["events"]:
        if isinstance(event, dict) and "date_start" in event and "series" in event and "track" in event:
            event_obj = {
                "date_start": str(event.get("date_start", "")).strip(),
                "date_end": str(event.get("date_end", event.get("date_start", ""))).strip(),
                "series": str(event.get("series", "")).strip(),
                "track": str(event.get("track", "")).strip(),
                "sessions": event.get("sessions", []) if isinstance(event.get("sessions"), list) else [],
                "source": str(event.get("source", "https://www.motogp.com/en/calendar")).strip(),
            }
            valid_events.append(event_obj)

    # Sortieren nach Startdatum
    valid_events.sort(key=lambda x: x["date_start"])

    # Nur für das erste (nächste) Event den Bike-Block erzeugen (FIX 5)
    if valid_events:
        bike = fetch_bike_of_weekend(valid_events[0], key)
        if bike:
            valid_events[0]["bike_of_weekend"] = bike

    output = {"events": valid_events}
    CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[race-update] Erfolgreich {len(valid_events)} Events in {CALENDAR_FILE} geschrieben.")


if __name__ == "__main__":
    update_calendar()
