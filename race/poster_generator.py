"""Erzeugt eigene Rennkalender-Grafiken mit optionalem abstraktem KI-Hintergrund."""
from __future__ import annotations

import base64
import os
import textwrap
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from asset_paths import get_poster_path, slugify
from .poster_style import research_style

LOG = Path("memory/RACE_POSTERS_LOG.md")
NANO_BANANA_MODEL = "gemini-3.1-flash-image"

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


def _nano_background(series: str, brief: str) -> Image.Image | None:
    """Erzeugt nur einen abstrakten Hintergrund, niemals Rennmaterial."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    prompt = f"""Create an original abstract background for a motorsport weekend calendar graphic.
Series context: {series}. Design brief: {brief}
Strict requirements: abstract shapes, gradients and light trails only; no people,
no motorcycle, no car, no track, no rider, no helmet, no team colors, no logos,
no brand names, no text, no numbers, no watermark. It must not resemble an
official poster or a photograph."""
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{NANO_BANANA_MODEL}:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=120,
        )
        if response.status_code != 200:
            print(f"Nano-Banana-Hintergrund nicht verfügbar: HTTP {response.status_code}")
            return None
        parts = response.json()["candidates"][0]["content"]["parts"]
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return Image.open(BytesIO(base64.b64decode(inline["data"]))).convert("RGB")
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print(f"Nano-Banana-Hintergrund nicht verfügbar: {error}")
    return None


def _draw_poster(series: str, details: str, size: tuple[int, int], background: Image.Image | None) -> Image.Image:
    key = "worldsbk" if "worldsbk" in series.lower() else "formel 1" if "formel" in series.lower() else "motogp"
    base_color, accent = COLORS[key]
    if background:
        image = background.resize(size)
        overlay = Image.new("RGBA", size, base_color + (205,))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    else:
        image = Image.new("RGB", size, base_color)
    draw = ImageDraw.Draw(image)
    width, height = size

    # Exakte Fakten kommen aus Pillow, nicht aus dem Bildmodell.
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
        "Eigene Kalendergrafik · Fakten vor dem Posten offiziell prüfen",
        font=small_font,
        fill=(200, 200, 200),
    )
    return image


def create_poster(series: str, details: str) -> list[Path]:
    """Erstellt eigene Grafiken; Nano Banana ist nur optionaler Hintergrund."""
    brief = research_style(series)
    background = _nano_background(series, brief)
    week = datetime.now().isocalendar().week
    outputs: list[Path] = []
    for suffix, size in (("feed", (1080, 1350)), ("story", (1080, 1920)), ("facebook", (1200, 630))):
        image = _draw_poster(series, details, size, background)
        path = get_poster_path(f"{slugify(series)}-{suffix}", week)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, quality=92)
        outputs.append(path)

    source = "Nano-Banana-Hintergrund" if background else "eigener Farbverlauf (Fallback)"
    old = LOG.read_text(encoding="utf-8") if LOG.exists() else "# Rennposter-Log\n"
    LOG.write_text(
        old.rstrip() + f"\n- {datetime.now():%Y-%m-%d %H:%M}: eigene Kalendergrafiken für {series} ({source})\n",
        encoding="utf-8",
    )
    return outputs
