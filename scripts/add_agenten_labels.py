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

def draw_text_with_shadow(draw, position, text, font, fill, shadow_color, anchor="mm", shadow_offset=(2, 2)):
    x, y = position
    sx, sy = shadow_offset
    draw.text((x + sx, y + sy), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def main():
    input_path = "assets/eigenes-material/agenten-team/agenten-team-2026-09-17.png"
    output_path = "assets/eigenes-material/agenten-team/agenten-team-2026-09-17-final.png"

    if not os.path.exists(input_path):
        print(f"Fehler: Bild nicht gefunden unter {input_path}")
        sys.exit(1)

    img = Image.open(input_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # 1. Titel oben (zweizeilig)
    title_font_size = int(H * 0.03)  # ca. 3% der Bildhöhe
    title_font = get_font("DejaVuSans-Bold.ttf", title_font_size)

    # Obere Zeile
    draw_text_with_shadow(
        draw,
        position=(W / 2, H * 0.04),
        text="BÜLENTS",
        font=title_font,
        fill="#1A1A1A",
        shadow_color="#FFFFFF",
        anchor="mm"
    )

    # Untere Zeile
    draw_text_with_shadow(
        draw,
        position=(W / 2, H * 0.08),
        text="BIKER LIFE AGENCY",
        font=title_font,
        fill="#1A1A1A",
        shadow_color="#FFFFFF",
        anchor="mm"
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
    label_font_size = int(H * 0.014)  # ca. 1.4% der Bildhöhe
    label_font = get_font("DejaVuSans-Bold.ttf", label_font_size)

    x_positions = [0.105, 0.245, 0.385, 0.505, 0.630, 0.755, 0.900]
    label_y = H * 0.745  # knapp unterhalb der weißen Sockel

    for i, label in enumerate(labels):
        x_pos = W * x_positions[i]
        draw.text((x_pos, label_y), label, font=label_font, fill="#3A3A3A", anchor="mm")

    # 3. Handle unten (unverändert)
    handle_text = "@edirnelibuelent"
    handle_font_size = int(H * 0.025)  # ~2.5% der Bildhöhe
    handle_font = get_font("DejaVuSans-Bold.ttf", handle_font_size)
    handle_y = H * 0.94

    draw.text((W / 2, handle_y), handle_text, font=handle_font, fill="#5A5A5A", anchor="mm")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Ergebnis erfolgreich gespeichert unter: {output_path}")

if __name__ == "__main__":
    main()
