"""Erzeugt ausschließlich Rennposter-Entwürfe – keine Veröffentlichung."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from asset_paths import get_poster_path, slugify
from generate_agnes_media import agnes_generate_image

LOG = Path("memory/RACE_POSTERS_LOG.md")
PROMPTS = {
    "motogp": "Cinematic MotoGP race poster, neon glow, dramatic dark background, prototype motorcycle in sharp cornering lean, futuristic HUD, ultra realistic professional motorsport photography",
    "worldsbk": "Superbike race atmosphere, dynamic cornering shot, motion blur, warm sunset lighting, Turkish flag colors accent, professional sports photography, hype poster style",
    "formel 1": "Cinematic Formula 1 poster, modern circuit at night, neon city lights, racing car in motion blur, dramatic sky, high contrast, ultra realistic",
}


def create_poster(series: str, details: str) -> list[Path]:
    key = "worldsbk" if "worldsbk" in series.lower() else "formel 1" if "formel" in series.lower() else "motogp"
    raw = agnes_generate_image(PROMPTS[key] + ". " + details)
    if not raw:
        return []

    image = Image.open(BytesIO(raw)).convert("RGB")
    week = datetime.now().isocalendar().week
    outputs: list[Path] = []
    for suffix, size in (("feed", (1080, 1350)), ("story", (1080, 1920)), ("facebook", (1200, 630))):
        canvas = image.resize(size)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, size[0], 120), fill=(0, 0, 0))
        draw.text((30, 35), f"Rennwochenende: {series.upper()}", fill="white", font=ImageFont.load_default())
        path = get_poster_path(f"{slugify(series)}-{suffix}", week)
        path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(path, quality=92)
        outputs.append(path)

    old = LOG.read_text(encoding="utf-8") if LOG.exists() else "# Rennposter-Log\n"
    LOG.write_text(old + f"\n- {datetime.now():%Y-%m-%d %H:%M}: Entwürfe für {series}\n", encoding="utf-8")
    return outputs
