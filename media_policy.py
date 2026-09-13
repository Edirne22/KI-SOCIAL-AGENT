"""Zentrale Medienrichtlinie für glaubwürdige Social-Media-Beiträge.

Bei realen Personen, Teams, Rennen und aktuellen Sportmeldungen dürfen keine
KI-generierten Bilder oder Videos als angebliche Aufnahme verwendet werden.
"""
from __future__ import annotations

import re

PROTECTED_TERMS = (
    "toprak", "razgatlioglu", "deniz öncü", "deniz oncu", "can öncü",
    "can oncu", "kenan sofuoglu", "bahattin sofuoglu", "zayn sofuoglu",
    "marc marquez", "pecco", "bagnaia", "jorge martin", "moto2",
    "motogp", "worldsbk", "moto gp", "pramac", "yamaha", "ducati",
    "rennen", "rennfahrer", "rennstrecke", "podium", "sprint",
    "startaufstellung", "grand prix", "misano",
)


def _text(block: str) -> str:
    match = re.search(r"(?ms)^Text:\s*(.*?)(?=^(?:Bild|Video|Bilder|Quelle|Medienstatus|Nutzungsrecht|Freigabe|Status|Publication-Claim):|\Z)", block)
    return match.group(1).strip() if match else block


def requires_verified_media(block: str) -> bool:
    """Ob die Aussage ein reales, nicht per KI zu bebilderndes Thema betrifft."""
    value = _text(block).lower()
    return any(term in value for term in PROTECTED_TERMS)


def ai_media_allowed(block: str) -> tuple[bool, str]:
    """Erlaubt KI-Medien nur für neutrale, nicht reale Themen."""
    if requires_verified_media(block):
        return False, (
            "reales Renn-/Personenthema erkannt – kein KI-Bild oder KI-Video. "
            "Nutze eigenes oder nachweislich freigegebenes Material."
        )
    return True, "neutrales Thema – KI-Medium zulässig"


def has_verified_media_rights(block: str) -> bool:
    """Prüft die explizite Freigabe für Medien bei geschützten Themen."""
    status = re.search(r"(?mi)^Medienstatus:\s*(.+?)\s*$", block)
    value = status.group(1).strip().upper() if status else ""
    if value == "EIGENES_MATERIAL":
        return True
    source = re.search(r"(?mi)^Quelle:\s*https?://\S+", block)
    rights = re.search(r"(?mi)^Nutzungsrecht:\s*BESTÄTIGT\s*$", block)
    return value == "QUELLE_BESTÄTIGT" and bool(source) and bool(rights)


def media_publishable(block: str) -> tuple[bool, str]:
    """Gibt frei, ob ein vorhandenes Medium veröffentlicht werden darf."""
    if not requires_verified_media(block):
        return True, "keine reale Renn-/Personenbehauptung"
    if has_verified_media_rights(block):
        return True, "Quelle bzw. eigene Mediennutzung bestätigt"
    return False, (
        "Medium blockiert: reale Person/Renn-News brauchen Quelle, "
        "Medienstatus: QUELLE_BESTÄTIGT (oder EIGENES_MATERIAL) und bei "
        "fremdem Material Nutzungsrecht: BESTÄTIGT."
    )
