"""Zentrale, sichere Pfadlogik für Medien-Assets."""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote

ASSETS = Path("assets")
RAW_BASE = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"
_TRANSLATION = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "ç": "c", "ğ": "g", "ı": "i", "ş": "s"})


class AssetResolutionError(ValueError):
    """Ein Asset fehlt oder der alte Dateiname ist nicht eindeutig."""


def slugify(text: str, max_length: int = 50) -> str:
    value = (text or "").lower()
    # Häufige türkische Eigennamen bleiben in ihrer geläufigen ASCII-Schreibweise lesbar.
    value = value.replace("öncü", "oncu")
    value = value.translate(_TRANSLATION)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return (value[:max_length].strip("-") or "motorrad-content")


def _month(day: date | None = None) -> str:
    return (day or date.today()).strftime("%Y-%m")


def get_image_path(slug: str, number: int = 1, day: date | None = None) -> Path:
    stamp = day or date.today()
    clean_slug = re.sub(r"-\\d{2}$", "", slugify(slug))
    return ASSETS / "images" / _month(stamp) / f"{stamp:%Y-%m-%d}-{clean_slug}-{number:02d}.jpg"


def get_video_path(slug: str, day: date | None = None) -> Path:
    stamp = day or date.today()
    return ASSETS / "videos" / _month(stamp) / f"{stamp:%Y-%m-%d}-{slugify(slug)}.mp4"


def get_carousel_dir(slug: str, day: date | None = None) -> Path:
    stamp = day or date.today()
    return ASSETS / "carousels" / f"{stamp:%Y-%m-%d}-{slugify(slug)}"


def get_poster_path(series: str, week: int | None = None, extension: str = "jpg") -> Path:
    stamp = date.today()
    calendar_week = week if week is not None else stamp.isocalendar().week
    return ASSETS / "race-posters" / f"{stamp.year}-W{calendar_week:02d}-{slugify(series)}.{extension.lstrip('.')}"


def get_published_path(day: date, platform: str, media_type: str, number: int = 1, extension: str = "jpg") -> Path:
    return ASSETS / "published" / _month(day) / (
        f"{day:%Y-%m-%d}-{slugify(platform)}-{slugify(media_type)}-{number:02d}.{extension.lstrip('.')}"
    )


def get_test_path(filename: str) -> Path:
    return ASSETS / "test" / Path(filename).name


def _safe_relative(value: str) -> Path:
    normalized = value.replace("\\", "/").strip().lstrip("./")
    candidate = Path(normalized)
    if not normalized or candidate.is_absolute() or ".." in candidate.parts:
        raise AssetResolutionError("Ungültiger Asset-Pfad.")
    return candidate


def resolve_asset(path_or_filename: str) -> str:
    """Löst neue Pfade sowie alte Dateinamen sicher und eindeutig auf."""
    candidate = _safe_relative(path_or_filename)
    if len(candidate.parts) > 1:
        # assets/ ist das neue Format; race-posters/ bleibt bis zur Migration als Legacy-Pfad lesbar.
        if candidate.parts[0] not in {"assets", "race-posters"}:
            raise AssetResolutionError("Vollständige Asset-Pfade müssen mit assets/ beginnen.")
        if not candidate.is_file():
            raise AssetResolutionError(f"Asset nicht gefunden: {candidate.as_posix()}")
        return candidate.as_posix()

    target = candidate.name.lower()
    roots = [Path("."), ASSETS / "images", ASSETS / "videos", ASSETS / "carousels", ASSETS / "user-assets", ASSETS / "published", ASSETS / "race-posters"]
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        iterator = root.glob("*") if root == Path(".") else root.rglob("*")
        for item in iterator:
            if item.is_file() and item.name.lower() == target:
                matches.append(item)
    unique = sorted({item.as_posix() for item in matches})
    if not unique:
        raise AssetResolutionError(f"Legacy-Asset nicht gefunden: {candidate.name}")
    if len(unique) > 1:
        raise AssetResolutionError("Legacy-Asset ist nicht eindeutig: " + ", ".join(unique))
    return unique[0].lstrip("./")


def asset_url(path_or_filename: str, raw_base: str = RAW_BASE) -> str:
    return raw_base.rstrip("/") + "/" + quote(resolve_asset(path_or_filename), safe="/")
