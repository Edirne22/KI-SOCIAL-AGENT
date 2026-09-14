"""Prüft öffentliche Rennquellen und erstellt nur bestätigte Poster-Entwürfe."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

import requests

from .poster_generator import create_poster
from .race_sources import SOURCES

OUT = Path("memory/RACE_WEEKEND.md")
PUBLISHED = Path("content/PUBLISHED.md")
EVENT_OVERRIDE = Path("config/RACE_EVENT_OVERRIDE.json")
MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash")


def collect() -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    for series, urls in SOURCES.items():
        available = []
        for url in urls:
            try:
                response = requests.get(url, timeout=20, headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"})
                if response.ok:
                    available.append(url)
            except requests.RequestException:
                continue
        data[series] = available
    return data



def confirmed_override() -> tuple[str, str] | None:
    """Liest einen zeitlich begrenzten, offiziell belegten Termin-Fallback."""
    if not EVENT_OVERRIDE.exists():
        return None
    try:
        event = json.loads(EVENT_OVERRIDE.read_text(encoding="utf-8"))
        valid_until = datetime.strptime(event["valid_until"], "%Y-%m-%d").date()
        if datetime.now().date() > valid_until:
            return None
        source = event["source"].strip()
        details = f'{event["details"].strip()} | Quelle: {source}'
        print(f"[race] Verwende bestätigten Termin-Fallback bis {valid_until}: {event['series']}")
        return event["series"].strip(), details
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"[race] Termin-Fallback ungültig, Online-Recherche wird verwendet: {error}")
        return None

def confirmed_weekend() -> tuple[str, str] | None:
    """Ermittelt das nächste Rennen ausschließlich mit belegbarer Quelle.

    Der Parser ist absichtlich tolerant: Gemini darf keine Markdown-Tabelle oder
    zusätzlichen Fließtext erzeugen, ohne dass deshalb ein bestätigter Termin
    verloren geht. Ohne positive Bestätigung wird weiterhin kein Entwurf erstellt.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("[race] GEMINI_API_KEY fehlt - Recherche nicht moeglich.")
        return None

    source_hints = "\n".join(
        f"- {series}: " + ", ".join(urls) for series, urls in SOURCES.items()
    )
    prompt = f"""Heute ist {datetime.now():%Y-%m-%d}. Ermittle das zeitlich nächste,
noch nicht begonnene Rennwochenende von MotoGP, WorldSBK oder Formel 1.

Nutze die Websuche und bestätige Datum, Strecke und Serie an einer offiziellen
Quelle. Diese Quellen sind bevorzugt:
{source_hints}

Antworte ohne Markdown und exakt mit diesen vier Zeilen:
BESTÄTIGT: ja
SERIE: <MotoGP | WorldSBK | Formel 1>
DETAILS: <offizieller Eventname> — <Strecke, Ort> — <TT. bis TT. Monat JJJJ>
QUELLE: <vollständige offizielle URL>

Wenn du keinen eindeutig bestätigten kommenden Termin findest, setze
BESTÄTIGT: nein. Erfinde keine Daten, Sessionzeiten oder Quellen."""
    text = ""
    for model in MODELS:
        print(f"[race] Prüfe Rennkalender mit Modell: {model}")
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
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                break
            print(f"[race] Modell {model}: HTTP {response.status_code}; nächstes Modell wird versucht.")
        except (requests.RequestException, KeyError, IndexError, ValueError) as error:
            print(f"[race] Modell {model}: {type(error).__name__}; nächstes Modell wird versucht.")
    if not text:
        print("[race] Rennkalender-Recherche derzeit nicht verfügbar; kein Entwurf erstellt.")
        return None

    confirmed = re.search(r"(?im)^\s*BESTÄTIGT\s*:\s*ja\s*$", text)
    series = re.search(r"(?im)^\s*SERIE\s*:\s*(.+?)\s*$", text)
    details = re.search(r"(?im)^\s*DETAILS\s*:\s*(.+?)\s*$", text)
    source = re.search(r"(?im)^\s*QUELLE\s*:\s*(https?://\S+)\s*$", text)
    if not (confirmed and series and details and source):
        print("[race] Kein ausreichend belegter kommender Renntermin gefunden; Entwurf übersprungen.")
        print(f"[race] Antwort (gekuerzt): {text[:800]}")
        return None

    # Die Quelle wird in die Details übernommen und bleibt so im Entwurf sichtbar.
    result_details = f"{details.group(1).strip()} | Quelle: {source.group(1).strip()}"
    print(f"[race] Bestaetigtes Rennwochenende: {series.group(1).strip()} / {result_details}")
    return (series.group(1).strip(), result_details)

def append_draft(series: str, details: str, posters: list[Path]) -> None:
    """Legt getrennte, normale Publisher-Blöcke an; Freigabe bleibt bei Bülent."""
    if len(posters) < 3:
        return
    existing = PUBLISHED.read_text(encoding="utf-8") if PUBLISHED.exists() else "# Freigegebene Beiträge\n"
    marker = f"Rennkalender: {datetime.now():%Y-W%W}-{series}"
    if marker in existing:
        return
    source = SOURCES.get(series, ["https://www.motogp.com/"])[0]
    common = (
        f"Status: ENTWURF\nFreigabe: Rennkalender\n{marker}\n"
        f"Titel: 🏁 {series} – Rennwochenende\nText: {details}\n"
        f"Quelle: {source}\nMedienstatus: EIGENES_MATERIAL\n"
    )
    entry = (
        f"\n## Instagram\n{common}Bild: {posters[0].as_posix()}\n"
        f"\n## Story\n{common}Bild: {posters[1].as_posix()}\n"
        f"\n## Facebook\n{common}Bild: {posters[2].as_posix()}\n"
    )
    PUBLISHED.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")


def main() -> None:
    sources = collect()
    found = confirmed_override() or confirmed_weekend()
    lines = ["# Nächstes Rennwochenende", f"Geprüft: {datetime.now():%Y-%m-%d %H:%M}", "", "> Zeiten bitte vor Veröffentlichung an der Originalquelle prüfen."]
    for series, urls in sources.items():
        lines += [f"\n## {series}", f"- Öffentliche Quellen erreichbar: {len(urls)}"]
    if not found:
        lines += ["", "Kein eindeutig bestätigtes Rennwochenende gefunden; kein Poster-Entwurf erzeugt."]
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Keine bestätigten Renndaten – Poster sicher übersprungen.")
        return
    series, details = found
    posters = create_poster(series, details)
    lines += ["", f"Bestätigt: {series}", f"Details: {details}", f"Poster-Entwürfe: {len(posters)}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_draft(series, details, posters)
    print("Bestätigter Rennkalender und Poster-Entwurf erstellt.")


if __name__ == "__main__":
    main()
