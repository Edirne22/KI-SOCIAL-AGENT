"""Aktualisiert memory/RACE_CALENDAR.json monatlich via Agnes (agnes-2.5-flash)."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests

CALENDAR_FILE = Path("memory/RACE_CALENDAR.json")

AGNES_URL = "https://apihub.agnes-ai.com/v1/chat/completions"
AGNES_MODEL = "agnes-2.5-flash"
RETRY_DELAYS = [5, 15, 30]

BRAND_FALLBACK_URLS = {
    "Ducati": "https://www.ducati.com/de/de/home",
    "Aprilia": "https://www.aprilia.com/de_DE/",
    "KTM": "https://www.ktm.com/de-de.html",
    "Honda": "https://www.honda.de/motorraeder.html",
    "Yamaha": "https://www.yamaha-motor.eu/de/de/",
    "BMW": "https://www.bmw-motorrad.de/de/home.html",
}

MOTOGP_BRANDS = ["Ducati", "Aprilia", "KTM", "Honda", "Yamaha"]
WSBK_BRANDS = ["BMW"]  # nur wenn Rennwochenende WorldSBK ist


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


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def extract_og_image(html: str, base_url: str) -> str | None:
    pattern_prop_first = r'<meta\s+[^>]*property=["\'](og:image|og:image:secure_url)["\']\s+content=["\']([^"\']+)["\']'
    match = re.search(pattern_prop_first, html, re.IGNORECASE)
    if match:
        return urljoin(base_url, match.group(2))

    pattern_content_first = r'<meta\s+[^>]*content=["\']([^"\']+)["\']\s+property=["\'](og:image|og:image:secure_url)["\']'
    match_rev = re.search(pattern_content_first, html, re.IGNORECASE)
    if match_rev:
        return urljoin(base_url, match_rev.group(1))

    return None


def verify_url(url: str) -> bool:
    try:
        resp = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        return resp.status_code == 200
    except Exception as err:
        print(f"[race-update] HEAD Request fehlgeschlagen für {url}: {err}")
        return False


def fetch_bike_of_weekend(event: dict, key: str) -> dict | None:
    series = event.get("series", "").strip()
    if series == "MotoGP":
        available_brands = MOTOGP_BRANDS
    elif series in ("WorldSBK", "WSBK"):
        available_brands = WSBK_BRANDS
    else:
        return None

    event_title = f"{series} {event.get('track', '')}".strip()
    prompt = f"""Rennwochenende: {event_title}
Strecke: {event.get('track', '')}
Serie: {series}
Verfügbare Hersteller: {', '.join(available_brands)}

Aufgabe: Wähle EINEN Hersteller, der inhaltlich zum Rennwochenende passt
(Heimrennen, aktuelle Performance, Serie). Recherchiere das passende aktuelle
Supersport-/Supernaked-Modell dieses Herstellers (Baujahr 2025 oder 2026,
Topmodell mit Rennsport-Bezug).

Schreibe 2–3 Sätze in folgender Stimme: direkt, community-nah, Motorrad-
Enthusiast, deutsch, ohne Marketingsprache. Erkläre in einem Satz, warum
das Bike zu diesem GP passt.

Liefere die offizielle Hersteller-Produktseite als source_url.

Antworte NUR mit JSON:
{{
  "brand": "KTM",
  "model": "1290 Super Duke R",
  "category": "Supernaked",
  "displacement_ccm": 1301,
  "story": "2-3 Sätze in Bülents Stimme...",
  "source_url": "https://www.ktm.com/de-de/models/naked-bikes/1290-super-duke-r.html"
}}"""

    bike_data = call_agnes_json(prompt, key)
    if not isinstance(bike_data, dict) or not bike_data.get("brand") or not bike_data.get("model"):
        print(f"[race-update] Warnung: Kein gültiges Bike von Agnes für Event {event_title} geliefert.")
        return None

    brand = str(bike_data.get("brand", "")).strip()
    model = str(bike_data.get("model", "")).strip()
    category = str(bike_data.get("category", "")).strip()
    displacement_ccm = bike_data.get("displacement_ccm")
    story = str(bike_data.get("story", "")).strip()
    source_url = str(bike_data.get("source_url", "")).strip()

    verified_url = None
    if source_url and verify_url(source_url):
        verified_url = source_url
    elif brand in BRAND_FALLBACK_URLS:
        fallback_url = BRAND_FALLBACK_URLS[brand]
        print(f"[race-update] source_url ungültig. Versuche Fallback-URL für {brand}: {fallback_url}")
        if verify_url(fallback_url):
            verified_url = fallback_url
        else:
            print(f"[race-update] Warnung: Auch Fallback-URL für {brand} schlug fehl.")

    if not verified_url:
        print(f"[race-update] Warnung: Bike {brand} {model} hat keine verifizierte URL.")

    image_local = None
    instagram_ok = False

    if verified_url:
        try:
            get_resp = requests.get(
                verified_url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            if get_resp.status_code == 200:
                og_image_url = extract_og_image(get_resp.text, verified_url)
                if og_image_url:
                    img_resp = requests.get(
                        og_image_url,
                        timeout=15,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    )
                    if img_resp.status_code == 200 and img_resp.content:
                        date_start = event.get("date_start", "")
                        ym = date_start[:7] if len(date_start) >= 7 else datetime.now().strftime("%Y-%m")
                        folder = Path("assets/images") / ym
                        folder.mkdir(parents=True, exist_ok=True)

                        brand_slug = slugify(brand)
                        model_slug = slugify(model)
                        filename = f"{date_start}-bike-{brand_slug}-{model_slug}.jpg"
                        img_path = folder / filename
                        img_path.write_bytes(img_resp.content)

                        try:
                            from PIL import Image

                            with Image.open(img_path) as img:
                                w, h = img.size
                            if w < 1000 or h < 1000:
                                instagram_ok = False
                                print(f"[race-update] Bike-Bild zu klein ({w}x{h}); Instagram überspringen.")
                            else:
                                instagram_ok = True
                            image_local = img_path.as_posix()
                        except Exception as img_err:
                            print(f"[race-update] Fehler bei Pillow Bildprüfung: {img_err}")
                            image_local = img_path.as_posix()
                            instagram_ok = False
                else:
                    print(f"[race-update] Warnung: Kein OpenGraph-Bild in {verified_url} gefunden.")
        except Exception as err:
            print(f"[race-update] Fehler bei OpenGraph-Extraktion/Bild-Download: {err}")

    bike_result = {
        "brand": brand,
        "model": model,
        "category": category,
        "displacement_ccm": displacement_ccm,
        "story": story,
    }
    if verified_url:
        bike_result["source_url"] = verified_url
    if image_local:
        bike_result["image_local"] = image_local
        bike_result["instagram_ok"] = instagram_ok

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

            # Optional: Bike of the Race Weekend
            bike = fetch_bike_of_weekend(event_obj, key)
            if bike:
                event_obj["bike_of_weekend"] = bike

            valid_events.append(event_obj)

    # Sortieren nach Startdatum
    valid_events.sort(key=lambda x: x["date_start"])

    output = {"events": valid_events}
    CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[race-update] Erfolgreich {len(valid_events)} Events in {CALENDAR_FILE} geschrieben.")


if __name__ == "__main__":
    update_calendar()
