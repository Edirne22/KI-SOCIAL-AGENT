"""Technische Medienreife für Veröffentlichungen.

Ein Post wird niemals wegen Namen, Quelle, Nutzungsrecht oder Medienstatus
blockiert. Für Bild-, Video- und Karussell-Formate zählt ausschließlich:
Ist ein konkreter Medienpfad statt `auto` eingetragen?
"""

from __future__ import annotations

import re


# Ausschließlich für die KI-Medienerzeugung, niemals für die Veröffentlichungsfreigabe.
# So entstehen keine KI-Bilder oder -Videos, die echte Rennaufnahmen vortäuschen.
REAL_RACE_TERMS = (
    "toprak", "razgatlioglu", "deniz öncü", "deniz oncu", "can öncü",
    "can oncu", "kenan sofuoglu", "marc marquez", "bagnaia",
    "jorge martin", "moto2", "motogp", "worldsbk", "moto gp",
    "pramac", "yamaha", "ducati", "rennen", "rennfahrer",
    "rennstrecke", "podium", "sprint", "grand prix", "misano",
)


def _media_paths(block: str) -> list[str]:
    """Liest nur konkrete Pfade; `Bild: auto`/`Video: auto` zählen nicht."""
    paths = re.findall(r"(?mi)^(?:Bild|Video):\s*(?!auto\s*$)(\S+)", block)
    for match in re.finditer(r"(?ms)^Bilder:\s*\n((?:\s*-\s*\S+[^\n]*\n?)+)", block):
        paths.extend(re.findall(r"(?m)^\s*-\s*(\S+)", match.group(1)))
    return [path.replace("\\", "/") for path in paths if path.strip()]


def has_verified_media_rights(block: str) -> bool:
    """Kompatibilitätsname: Ein konkreter Medienpfad genügt vollständig."""
    return bool(_media_paths(block))


def media_publishable(block: str) -> tuple[bool, str]:
    """Keine Quellen- oder Rechteprüfung; nur konkrete Medienpfade sind relevant."""
    if _media_paths(block):
        return True, "Konkreter Medienpfad vorhanden."
    return True, "Kein konkreter Medienpfad vorhanden."


def ai_media_allowed(block: str) -> tuple[bool, str]:
    """Verhindert nur künstliche Bilder/Videos, die echte Rennaufnahmen vortäuschen."""
    has_auto_medium = bool(re.search(r"(?mi)^(?:Bild|Video):\s*auto\s*$", block))
    text = block.lower()
    if has_auto_medium and any(term in text for term in REAL_RACE_TERMS):
        return False, (
            "Kein KI-Medium für reale Rennaufnahme. Lade bei Bedarf stattdessen "
            "dein eigenes Bild oder Video hoch."
        )
    return True, "KI-Medium zulässig."
