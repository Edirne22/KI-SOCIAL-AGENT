"""Curated technical research input for the first Quickshifter acceptance film.

Technical explainer backed by manufacturer documentation.\nSource references are specific and evergreen, not fabricated news.
"""
from __future__ import annotations

from datetime import datetime, timezone


def quickshifter_research() -> dict:
    source = "https://www.ktm.com/en-dk/tech-guide/quickshifter.html"
    segments = [
        ("Schalten ohne Kupplungshebel", "Ein Quickshifter unterstützt Gangwechsel während der Fahrt, ohne dass der Fahrer den Kupplungshebel betätigen muss."),
        ("Sensor erkennt den Schaltwunsch", "Ein Sensor am Schaltgestänge erkennt den Schaltimpuls und gibt ihn an die elektronische Steuerung weiter."),
        ("Drehmoment kurz entlasten", "Beim Hochschalten kann die Motorsteuerung das Antriebsmoment kurz reduzieren, etwa durch Eingriffe in Zündung oder Einspritzung."),
        ("Gangwechsel im Getriebe", "Durch die kurze Entlastung kann der nächste Gang leichter eingelegt werden. Die genaue Funktion hängt vom Motorrad und System ab."),
        ("Runterschalten ist anders", "Ein Blipper kann beim Herunterschalten die Motordrehzahl anpassen. Nicht jeder Quickshifter unterstützt beide Richtungen."),
    ]
    return {
        "prompt": "Wie funktioniert ein Motorrad-Quickshifter?",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(segments),
        "stories": [
            {
                "story_id": f"quickshifter-{i}",
                "title": title,
                "summary": summary,
                "original_url": source,
                "source_name": "KTM Quickshifter+ technical guide",
                "source_status": "official",
                "content_type": "technical_explainer",
                "series": "Motorradtechnik",
                "confirmed_facts": [],
                "unconfirmed_statements": [],
                "media_license": "synthetic_fallback",
            }
            for i, (title, summary) in enumerate(segments, start=1)
        ],
    }
