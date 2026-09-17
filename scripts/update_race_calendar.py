"""Aktualisiert memory/RACE_CALENDAR.json monatlich via Gemini (mit google_search)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

CALENDAR_FILE = Path("memory/RACE_CALENDAR.json")
MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash")


def update_calendar() -> None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("[race-update] GEMINI_API_KEY fehlt - Kalender-Update nicht möglich.")
        sys.exit(1)

    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Heute ist {today_str}. Recherche per Websuche die kommenden 4 Rennwochenenden von MotoGP, WorldSBK oder Formel 1.

Gib ausschließlich ein valides JSON-Objekt zurück (ohne Markdown ```json ... ```-Wrapper, ohne zusätzlichen Text), das exakt folgender Struktur entspricht:

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

    text = ""
    for model in MODELS:
        print(f"[race-update] Recherche Rennkalender mit Modell: {model}")
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"Content-Type": "application/json", "X-goog-api-key": key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
                },
                timeout=120,
            )
            if response.status_code == 200:
                raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Entferne eventuelle Markdown Codeblock Formatting
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[-1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("```", 1)[0]
                text = raw_text.strip()
                break
            print(f"[race-update] Modell {model}: HTTP {response.status_code}; nächstes Modell wird versucht.")
        except (requests.RequestException, KeyError, IndexError, ValueError) as error:
            print(f"[race-update] Modell {model}: {type(error).__name__}; nächstes Modell wird versucht.")

    if not text:
        print("[race-update] Gemini-Recherche fehlgeschlagen. Abbruch.")
        sys.exit(1)

    try:
        data = json.loads(text)
        if "events" not in data or not isinstance(data["events"], list):
            raise ValueError("Antwort enthält kein 'events'-Array")

        # Validierung & Normalisierung
        valid_events = []
        for event in data["events"]:
            if "date_start" in event and "series" in event and "track" in event:
                valid_events.append({
                    "date_start": str(event.get("date_start", "")).strip(),
                    "date_end": str(event.get("date_end", event.get("date_start", ""))).strip(),
                    "series": str(event.get("series", "")).strip(),
                    "track": str(event.get("track", "")).strip(),
                    "sessions": event.get("sessions", []) if isinstance(event.get("sessions"), list) else [],
                    "source": str(event.get("source", "https://www.motogp.com/en/calendar")).strip()
                })

        # Sortieren nach Startdatum
        valid_events.sort(key=lambda x: x["date_start"])

        output = {"events": valid_events}
        CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALENDAR_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[race-update] Erfogreich {len(valid_events)} Events in {CALENDAR_FILE} geschrieben.")

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[race-update] Fehler beim Parsen des JSON von Gemini: {e}")
        print(f"[race-update] Rohtext war:\n{text[:500]}")
        sys.exit(1)


if __name__ == "__main__":
    update_calendar()
