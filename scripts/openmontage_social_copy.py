"""Deterministic, review-only social copy for verified OpenMontage research.

Never publishes and never invents race winners, team names or hashtags.
"""
from __future__ import annotations

import re


def build_social_copy(verified_research: dict, *, language: str = "de") -> dict:
    stories = verified_research.get("stories") or []
    if not stories or not verified_research.get("verified_item_count"):
        raise ValueError("Verified research required for captions")
    first = stories[0]
    title = re.sub(r"\\s+", " ", str(first.get("title") or "")).strip()
    if not title:
        raise ValueError("Missing verified story title")
    technical = any(x.get("content_type") == "technical_explainer" for x in stories)
    series = str(first.get("series") or "Motorsport")
    if language != "de":
        raise ValueError("Only verified German copy templates are supported")
    hashtags = ["#Motorrad", "#Motorradtechnik", "#Quickshifter", "#BikerDeutschland"] if technical else (
        ["#MotoGP", "#Motorsport", "#Racing", "#Motorrad"] if "motogp" in series.casefold()
        else ["#WorldSBK", "#Superbike", "#Motorsport", "#Racing"])
    summary = re.sub(r"\\s+", " ", str(first.get("summary") or "")).strip()
    if not summary:
        raise ValueError("Missing verified summary")
    intro = f"{title} 🏍️⚙️" if technical else f"{title} 🏁🔥"
    return {
        "status": "DRAFT_AWAITING_OWNER_APPROVAL",
        "voice_profile": "buelent_locker_flockig_chillig_v1",
        "avatar_ready_future": False,
        "instagram": {"caption": f"{intro}\\n{summary}\\n\\nSchon mal ausprobiert? Schreib mal, wie du das siehst! 😎👇\\n" + " ".join(hashtags),
                      "hashtags": hashtags},
        "facebook": {"caption": f"{title} 🏍️\\n\\n{summary}\\n\\nWie läuft das bei euch? Bin gespannt auf eure Erfahrungen! 😎\\n" + " ".join(hashtags[:3]),
                     "hashtags": hashtags[:3]},
        "publication_authorized": False,
    }
