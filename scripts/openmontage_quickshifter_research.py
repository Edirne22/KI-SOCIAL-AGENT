"""Curated technical research input for the first Quickshifter acceptance film.

This is a draft technical outline, not a verified research result.\nIt must not enter the rendering handoff before source verification.
"""
from __future__ import annotations

from datetime import datetime, timezone


def quickshifter_research() -> dict:
    source = "https://www.bosch-mobility.com/en/solutions/two-wheeler-and-powersports/"
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
                "source_name": "Bosch Mobility – Two-wheeler and Powersports",
                "source_status": "unverified_draft",
                "content_type": "technical_explainer",
                "series": "Motorradtechnik",
                "confirmed_facts": [],
                "unconfirmed_statements": [],
                "media_license": "synthetic_fallback",
            }
            for i, (title, summary) in enumerate(segments, start=1)
        ],
    }
