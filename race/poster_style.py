"""Erstellt einen eigenen, abstrakten Design-Brief für Rennkalendergrafiken.

Es werden nur allgemeine Gestaltungsmerkmale ausgewertet. Keine fremden Bilder,
Logos, Texte oder Layouts werden kopiert.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import requests

STYLE_LOG = Path("memory/RACE_POSTER_STYLE.md")
MODEL = "gemini-3.8-flash"


def research_style(series: str) -> str:
    """Recherchiert nur Layout-Prinzipien und fällt bei API-Ausfall sicher zurück."""
    fallback = (
        "Dunkler ruhiger Hintergrund, ein klarer Akzentstreifen, große Serienbezeichnung, "
        "viel freier Raum und gut lesbare Kalenderdaten. Keine Logos, keine Fahrerbilder."
    )
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return fallback

    prompt = f"""Analysiere öffentliche Motorsport- und Rennkalendergrafiken ausschließlich
auf allgemeine Gestaltungsprinzipien für eine eigene {series}-Wochenendgrafik.
Nenne maximal vier abstrakte Aspekte: Farbkontrast, Informationshierarchie,
Freiraum und Akzentform. Kopiere keine Namen, Logos, Slogans, konkreten Texte,
Bilder oder wiedererkennbaren Layouts. Die Antwort muss für eine neue,
eigenständige Grafik nutzbar sein."""
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
            },
            timeout=60,
        )
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
        brief = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        brief = " ".join(brief.split())[:700] or fallback
    except (requests.RequestException, KeyError, IndexError, RuntimeError) as error:
        print(f"Poster-Stilrecherche nicht verfügbar: {error}")
        brief = fallback

    old = STYLE_LOG.read_text(encoding="utf-8") if STYLE_LOG.exists() else "# Poster-Stilrecherche\n"
    entry = (
        f"\n## {datetime.now():%Y-%m-%d %H:%M} – {series}\n"
        f"- Nur abstrakte Inspiration, kein Fremdmaterial.\n"
        f"- Brief: {brief}\n"
    )
    STYLE_LOG.write_text(old.rstrip() + entry + "\n", encoding="utf-8")
    return brief
