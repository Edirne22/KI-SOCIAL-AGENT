"""Erzeugt eigene sachliche Rennkalender-Grafiken – keine KI-Rennbilder."""
from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from asset_paths import get_poster_path, slugify

LOG = Path("memory/RACE_POSTERS_LOG.md")

COLORS = {
    "motogp": ((17, 24, 39), (220, 38, 38)),
    "worldsbk": ((15, 58, 95), (14, 165, 233)),
    "formel 1": ((49, 10, 10), (239, 68, 68)),
}


def _font(size: int, bold: bool = False):
    names = (
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _draw_poster(series: str, details: str, size: tuple[int, int]) -> Image.Image:
    key = "worldsbk" if "worldsbk" in series.lower() else "formel 1" if "formel" in series.lower() else "motogp"
    background, accent = COLORS[key]
    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    width, height = size

    # Eigenes grafisches Design: Linien, Typografie und Kalenderdaten statt Rennfoto.
    draw.rectangle((0, 0, width, int(height * 0.045)), fill=accent)
    draw.rectangle((int(width * 0.08), int(height * 0.19), int(width * 0.12), int(height * 0.76)), fill=accent)
    title_font = _font(max(28, width // 15), bold=True)
    body_font = _font(max(20, width // 31), bold=False)
    small_font = _font(max(14, width // 48), bold=False)

    draw.text((int(width * 0.18), int(height * 0.17)), "RENNWOCHENENDE", font=small_font, fill=(220, 220, 220))
    draw.text((int(width * 0.18), int(height * 0.25)), series.upper(), font=title_font, fill="white")

    y = int(height * 0.48)
    for line in textwrap.wrap(details, width=28):
        draw.text((int(width * 0.18), y), line, font=body_font, fill=(245, 245, 245))
        y += int(body_font.size * 1.35)

    draw.text(
        (int(width * 0.18), int(height * 0.86)),
        "Kalendergrafik · Fakten vor dem Posten an offizieller Quelle prüfen",
        font=small_font,
        fill=(200, 200, 200),
    )
    return image


def create_poster(series: str, details: str) -> list[Path]:
    """Erstellt eigene Informationsgrafiken ohne fremde oder KI-generierte Rennmotive."""
    week = datetime.now().isocalendar().week
    outputs: list[Path] = []
    for suffix, size in (("feed", (1080, 1350)), ("story", (1080, 1920)), ("facebook", (1200, 630))):
        image = _draw_poster(series, details, size)
        path = get_poster_path(f"{slugify(series)}-{suffix}", week)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, quality=92)
        outputs.append(path)

    old = LOG.read_text(encoding="utf-8") if LOG.exists() else "# Rennposter-Log\n"
    LOG.write_text(
        old.rstrip() + f"\n- {datetime.now():%Y-%m-%d %H:%M}: eigene Kalendergrafiken für {series}\n",
        encoding="utf-8",
    )
    return outputs
