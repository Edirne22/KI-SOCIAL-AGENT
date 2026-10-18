"""Motorsport research source catalog: discovery hints, never pre-verified facts.

Factual driver/team/track/calendar assertions must be extracted from dated
sources on each job, not inferred from this static catalog.
"""
from __future__ import annotations

SOURCES = (
    {"name": "MotoGP", "url": "https://www.motogp.com/", "series": "MotoGP", "topics": ("calendar", "riders", "teams", "results", "circuits", "news"), "tier": "official"},
    {"name": "MotoGP results", "url": "https://www.motogp.com/en/gp-results", "series": "MotoGP", "topics": ("results", "timing"), "tier": "official"},
    {"name": "WorldSBK", "url": "https://www.worldsbk.com/", "series": "WorldSBK", "topics": ("calendar", "riders", "teams", "results", "circuits", "WorldSSP"), "tier": "official"},
    {"name": "FIM", "url": "https://www.fim-moto.com/", "series": "all", "topics": ("regulations", "championships"), "tier": "official"},
    {"name": "Turkish Motorcycle Federation", "url": "https://www.tmf.org.tr/", "series": "Turkish racing", "topics": ("riders", "calendar", "results"), "tier": "official"},
    {"name": "BMW Motorrad", "url": "https://www.bmw-motorrad.com/", "series": "technical", "topics": ("motorcycle technology", "quickshifter"), "tier": "manufacturer"},
    {"name": "KTM", "url": "https://www.ktm.com/", "series": "technical", "topics": ("motorcycle technology", "quickshifter"), "tier": "manufacturer"},
    {"name": "Honda", "url": "https://global.honda/en/motorcycle/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "Yamaha", "url": "https://global.yamaha-motor.com/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "Ducati", "url": "https://www.ducati.com/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "Kawasaki", "url": "https://www.kawasaki.eu/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "Suzuki", "url": "https://www.globalsuzuki.com/motorcycle/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "Harley-Davidson", "url": "https://www.harley-davidson.com/", "series": "technical", "topics": ("motorcycle technology",), "tier": "manufacturer"},
    {"name": "TRF1", "url": "https://trf1.net/", "series": "Turkish racing", "topics": ("news", "analysis"), "tier": "secondary"},
    {"name": "MotoEtkinlik", "url": "https://motoetkinlik.com/", "series": "Turkish racing", "topics": ("news", "events"), "tier": "secondary"},
)

REFRESH_POLICIES = {
    "riders": "check official current-season roster before each film",
    "teams": "check official current-season roster before each film",
    "circuits": "check official season calendar; distinguish historical vs scheduled",
    "calendar": "check official calendar and changes before scheduling",
    "results": "check official classification and race date before narration",
    "technology": "check model/year-specific manufacturer documentation and precise claim",
}


def find_sources(topic: str, series: str | None = None) -> list[dict]:
    key = topic.casefold()
    return [dict(item) for item in SOURCES
            if (series is None or item["series"].casefold() in (series.casefold(), "all"))
            and any(key in term.casefold() or term.casefold() in key for term in item["topics"])]


def source_catalog_memory_lesson() -> str:
    return ("Recherchequellen-Verzeichnis im Code: integrations/openmontage/motorsport_source_catalog.py. "
            "Für Fahrer, Teams, Rennstrecken, Kalender und Resultate offizielle Saisonseiten aktuell abfragen; "
            "Hersteller für technische Details, TRF1/MotoEtkinlik als Hinweise. "
            "Katalog-URLs sind Startpunkte, keine verifizierten Einzelfakten. "
            "Suchmaschine nur zur Entdeckung weiterer Primärquellen, nicht als Wahrheitsbeleg.")
