import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size):
    font_candidates = [
        font_name,
        f"/usr/share/fonts/truetype/dejavu/{font_name}",
        f"/usr/share/fonts/truetype/liberation/{font_name}",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "Arial.ttf"
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

def draw_centered_text(draw, text, font, fill, y_pos, image_width, shadow=False, shadow_color="#888888"):
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x_pos = (image_width - text_width) / 2
    if shadow:
        draw.text((x_pos + 2, y_pos + 2), text, font=font, fill=shadow_color)
    draw.text((x_pos, y_pos), text, font=font, fill=fill)

def draw_agent_label(draw, text, font, fill, center_x, y_pos):
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    x_pos = center_x - (text_width / 2)
    draw.text((x_pos, y_pos), text, font=font, fill=fill)

def main():
    input_path = "assets/eigenes-material/agenten-team/agenten-team-2026-09-17.png"
    output_path = "assets/eigenes-material/agenten-team/agenten-team-2026-09-17-final.png"

    if not os.path.exists(input_path):
        print(f"Fehler: Bild nicht gefunden unter {input_path}")
        sys.exit(1)

    img = Image.open(input_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # 1. Titel oben
    title_text = "BÜLENTS BIKER LIFE AGENCY"
    title_font_size = int(H * 0.04)  # ~4% der Bildhöhe
    title_font = get_font("DejaVuSans-Bold.ttf", title_font_size)
    title_y = int(H * 0.035)  # ~3.5% vom oberen Rand
    draw_centered_text(
        draw,
        title_text,
        title_font,
        fill="#2B2B2B",
        y_pos=title_y,
        image_width=W,
        shadow=True,
        shadow_color="#D0D0D0"
    )

    # 2. Agenten-Labels
    labels = [
        "Recherche",
        "Content",
        "Kurator",
        "Video",
        "Analyse",
        "Qualität",
        "Publisher"
    ]
    label_font_size = int(H * 0.02)  # ~2% der Bildhöhe
    label_font = get_font("DejaVuSans-Bold.ttf", label_font_size)
    label_y = int(H * 0.73)  # Knapp unter den weißen Sockeln (~73% der Bildhöhe)

    for i, label in enumerate(labels):
        center_x = W * (i + 0.5) / 7.0
        draw_agent_label(draw, label, label_font, fill="#3A3A3A", center_x=center_x, y_pos=label_y)

    # 3. Handle unten
    handle_text = "@edirnelibuelent"
    handle_font_size = int(H * 0.025)  # ~2.5% der Bildhöhe
    handle_font = get_font("DejaVuSans-Bold.ttf", handle_font_size)
    handle_y = int(H * 0.94)  # ~3-5% vom unteren Rand
    draw_centered_text(
        draw,
        handle_text,
        handle_font,
        fill="#5A5A5A",
        y_pos=handle_y,
        image_width=W,
        shadow=False
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Ergebnis erfolgreich gespeichert unter: {output_path}")

if __name__ == "__main__":
    main()
