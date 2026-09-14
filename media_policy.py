"""Medienfreigabe über klare Ordner statt über Schlüsselwörter im Beitragstext.

Ein Fahrername oder Rennbegriff blockiert keinen Post. Entscheidend ist nur,
ob das tatsächlich angehängte Medium in einem eigenen oder einmalig
freigegebenen Quellenordner liegt. KI-Medien für reale Rennaufnahmen bleiben
gesondert gesperrt, damit keine falschen Motorsportbilder entstehen.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath


TRUSTED_SOURCES = Path("config/TRUSTED_MEDIA_SOURCES.json")
OWN_MEDIA_ROOT = ("assets", "eigenes-material")
TRUSTED_MEDIA_ROOT = ("assets", "freigegeben")

# Ausschließlich für die KI-Medienerzeugung, nicht für die Veröffentlichungsfreigabe.
REAL_RACE_TERMS = (
    "toprak", "razgatlioglu", "deniz öncü", "deniz oncu", "can öncü",
    "can oncu", "kenan sofuoglu", "marc marquez", "bagnaia",
    "jorge martin", "moto2", "motogp", "worldsbk", "moto gp",
    "pramac", "yamaha", "ducati", "rennen", "rennfahrer",
    "rennstrecke", "podium", "sprint", "grand prix", "misano",
)


def _media_paths(block: str) -> list[str]:
    paths = re.findall(r"(?mi)^(?:Bild|Video):\s*(?!auto\s*$)(\S+)", block)
    for match in re.finditer(r"(?ms)^Bilder:\s*\n((?:\s*-\s*\S+[^\n]*\n?)+)", block):
        paths.extend(re.findall(r"(?m)^\s*-\s*(\S+)", match.group(1)))
    return [path.replace("\\", "/") for path in paths if path.strip()]


def _trusted_sources() -> dict:
    try:
        data = json.loads(TRUSTED_SOURCES.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _is_precleared_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if parts[:2] == OWN_MEDIA_ROOT:
        return True
    if len(parts) < 4 or parts[:2] != TRUSTED_MEDIA_ROOT:
        return False
    source = _trusted_sources().get(parts[2], {})
    return isinstance(source, dict) and source.get("status") == "CONFIRMED_BY_BUELENT"


def has_verified_media_rights(block: str) -> bool:
    """Akzeptiert vorhandene Alt-Metadaten oder vorab freigegebene Medienpfade."""
    status = re.search(r"(?mi)^Medienstatus:\s*(.+?)\s*$", block)
    value = status.group(1).strip().upper() if status else ""
    if value == "EIGENES_MATERIAL":
        return True
    source = re.search(r"(?mi)^Quelle:\s*https?://\S+", block)
    rights = re.search(r"(?mi)^Nutzungsrecht:\s*BESTÄTIGT\s*$", block)
    if value == "QUELLE_BESTÄTIGT" and source and rights:
        return True
    paths = _media_paths(block)
    return bool(paths) and all(_is_precleared_path(path) for path in paths)


def media_publishable(block: str) -> tuple[bool, str]:
    """Prüft nur das angehängte Medium, niemals Personen- oder Rennbegriffe."""
    paths = _media_paths(block)
    if not paths:
        return True, "kein Medium vorhanden"
    if has_verified_media_rights(block):
        return True, "Medium liegt in einem freigegebenen Medienpfad"
    return False, (
        "Medium blockiert: Lege es unter assets/eigenes-material/ oder unter "
        "assets/freigegeben/<quelle>/ ab. Ein Fahrername im Text ist kein Blocker."
    )


def ai_media_allowed(block: str) -> tuple[bool, str]:
    """Verhindert nur künstliche Bilder/Videos, die echte Rennaufnahmen vortäuschen."""
    has_auto_medium = bool(re.search(r"(?mi)^(?:Bild|Video):\s*auto\s*$", block))
    text = block.lower()
    if has_auto_medium and any(term in text for term in REAL_RACE_TERMS):
        return False, (
            "Kein KI-Medium für reale Rennaufnahme. Lade stattdessen ein echtes "
            "Medium in einen freigegebenen Ordner hoch."
        )
    return True, "KI-Medium zulässig"