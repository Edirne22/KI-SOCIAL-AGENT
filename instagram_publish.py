import os
import re
import time
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import urljoin

from pathlib import Path
from PIL import Image
from asset_paths import asset_url, resolve_asset
from datetime import datetime

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"

HUMAN_WRITING_PROTOCOL = Path("config/HUMAN_WRITING_PROTOCOL.md")
MOTOGP_VOICE_RULES = Path("memory/MOTOGP_VOICE_RULES.md")


def extract_og_image_url(source_url):
    """Liest og:image aus der Quellseite. Fehler liefern None, damit Agnes übernehmen kann."""
    if not source_url or not source_url.startswith(("http://", "https://")):
        return None
    try:
        response = requests.get(
            source_url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 KI-SOCIAL-AGENT/1.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find("meta", attrs={"property": "og:image"})
        if not tag:
            tag = soup.find("meta", attrs={"name": "og:image"})
        value = (tag.get("content") or "").strip() if tag else ""
        return urljoin(source_url, value) if value else None
    except (requests.RequestException, ValueError, TypeError) as exc:
        print(f"INSTAGRAM OG IMAGE: Quelle nicht lesbar: {exc}")
        return None


def download_og_image_for_instagram(source_url, output_path):
    """Lädt og:image und schreibt es ohne Crop als 1080x1350 JPEG mit schwarzem Padding."""
    image_url = extract_og_image_url(source_url)
    if not image_url:
        return None
    try:
        response = requests.get(
            image_url,
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0 KI-SOCIAL-AGENT/1.0"},
        )
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as source:
            source.load()
            image = source.convert("RGB")
        image.thumbnail((1080, 1350), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (1080, 1350), "black")
        x = (1080 - image.width) // 2
        y = (1350 - image.height) // 2
        canvas.paste(image, (x, y))

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix.lower() not in {".jpg", ".jpeg"}:
            target = target.with_suffix(".jpg")
        canvas.save(target, "JPEG", quality=92, optimize=True)
        print(f"INSTAGRAM OG IMAGE: {image_url} -> {target} (1080x1350, Padding)")
        return target.as_posix()
    except (requests.RequestException, OSError, ValueError) as exc:
        print(f"INSTAGRAM OG IMAGE: Download/Formatierung fehlgeschlagen: {exc}")
        return None


def generate_buelent_caption(facebook_caption):
    """Formuliert nur den vorhandenen Facebook-Text um; bei LLM-Fehler bleibt er unverändert."""
    base = (facebook_caption or "").strip()
    if not base:
        return base
    try:
        from llm_router import quick_chat

        human = HUMAN_WRITING_PROTOCOL.read_text(encoding="utf-8") if HUMAN_WRITING_PROTOCOL.exists() else ""
        voice = MOTOGP_VOICE_RULES.read_text(encoding="utf-8") if MOTOGP_VOICE_RULES.exists() else ""
        prompt = f"""Schreibe die folgende deutsche Facebook-Caption fuer Instagram im Stil von Buelents Bike Life um.

VERBINDLICH:
- Nur umformulieren. KEINE neue Tatsacheninformation, Zahl, Person, Wertung, Behauptung oder Quelle einfuehren.
- Vorhandene Quellenangabe/URL muss erhalten bleiben, falls sie im Ausgangstext steht.
- Natuerliches Deutsch, direkt, motorradnah und communityorientiert.
- Gib ausschliesslich die fertige Caption aus, keine Erklaerung.

HUMAN WRITING PROTOCOL:
{human}

MOTOGP VOICE RULES:
{voice}

FACEBOOK-CAPTION:
{base}
"""
        result = quick_chat(prompt, task_type="final_captions")
        cleaned = (result or "").strip()
        return cleaned if cleaned else base
    except Exception as exc:
        print(f"INSTAGRAM CAPTION: LLM fehlgeschlagen, Facebook-Caption wird verwendet: {exc}")
        return base


def process_image_for_instagram(image_file):
    """Prüft das Bild auf Instagram Feed-Konformität und führt ggf. Center-Crop durch."""
    try:
        resolved_str = resolve_asset(image_file)
        local_path = Path(resolved_str)
    except Exception as e:
        print(f"Fehler: Bild-Pfad konnte nicht aufgelöst werden: {image_file} ({e})")
        raise SystemExit(1)

    if not local_path.is_file():
        print(f"Fehler: Bilddatei existiert nicht: {local_path}")
        raise SystemExit(1)

    try:
        with Image.open(local_path) as img:
            img.verify()
        img = Image.open(local_path)
    except Exception as e:
        print(f"Fehler: Bilddatei ist beschädigt oder kann nicht geöffnet werden: {local_path} ({e})")
        raise SystemExit(1)

    width, height = img.size
    if width <= 0 or height <= 0:
        print(f"Fehler: Ungültige Bild-Dimensionen ({width}x{height}) bei {local_path}")
        raise SystemExit(1)

    ratio = width / height

    # Erlaubte Instagram-Formate (Quadrat 1:1, Hochformat 4:5, Querformat 1.91:1) mit ±2% Toleranz
    targets = [
        (1.0, "1:1"),
        (0.8, "4:5"),
        (1.91, "1.91:1"),
    ]

    is_compliant = any(abs(ratio - target_ratio) / target_ratio <= 0.02 for target_ratio, _ in targets)

    if is_compliant:
        print(f"INSTAGRAM IMAGE CHECK: {local_path.name} {width}x{height} ratio={ratio:.4f} → konform → unverändert")
        return image_file

    # Zielformat bestimmen: Center-Crop auf das am besten passende Format
    if ratio < 0.8:
        # Höher als 4:5 (z. B. 1080x1920 Story-Format) -> Crop auf 4:5
        target_ratio, target_name = 0.8, "4:5"
    elif ratio > 1.91:
        # Breiter als 1.91:1 -> Crop auf 1.91:1
        target_ratio, target_name = 1.91, "1.91:1"
    else:
        # Dazwischen (z. B. 3:2 = 1.5 oder 16:9 = 1.77) -> Nächstgelegenes erlaubtes Format
        target_ratio, target_name = min(targets, key=lambda t: abs(ratio - t[0]))

    if ratio < target_ratio:
        # Bild ist zu hoch für das Zielverhältnis -> in der Höhe beschneiden
        crop_width = width
        crop_height = int(round(width / target_ratio))
    else:
        # Bild ist zu breit für das Zielverhältnis -> in der Breite beschneiden
        crop_height = height
        crop_width = int(round(height * target_ratio))

    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    right = left + crop_width
    bottom = top + crop_height

    cropped_img = img.crop((left, top, right, bottom))
    if cropped_img.mode in ("RGBA", "P"):
        cropped_img = cropped_img.convert("RGB")

    new_filename = f"{local_path.stem}-ig-resized.jpg"
    new_local_path = local_path.parent / new_filename

    cropped_img.save(new_local_path, "JPEG", quality=90)
    out_w, out_h = cropped_img.size

    print(f"INSTAGRAM IMAGE CHECK: {local_path.name} {width}x{height} ratio={ratio:.4f} → ausserhalb → crop auf {target_name} → {new_filename} {out_w}x{out_h}")

    # Relative Pfadangabe basierend auf dem übergebenen image_file für asset_url zurückgeben
    orig_path = Path(image_file)
    new_relative_path = (orig_path.parent / new_filename).as_posix() if orig_path.parent != Path(".") else new_filename
    return new_relative_path

def check_media_status_warning(block: str) -> None:
    titel_match = re.search(r"(?mi)^Titel:\s*(.+)$", block)
    block_title = titel_match.group(1).strip() if titel_match else block.splitlines()[0].strip()
    ms_match = re.search(r"(?mi)^Medienstatus:\s*(.+)$", block)
    nr_match = re.search(r"(?mi)^Nutzungsrecht:\s*(.+)$", block)
    ms_val = ms_match.group(1).strip() if ms_match else "FEHLEND"
    nr_val = nr_match.group(1).strip() if nr_match else None
    known_statuses = {"EIGENES_MATERIAL", "EIGENE_KI_EDITORIALGRAFIK", "KI_ERLAUBT", "QUELLE_BESTÄTIGT"}
    if ms_val == "QUELLE_PRÜFEN" or ms_val not in known_statuses or not nr_val:
        print(f"WARNUNG: Block {block_title} hatte Medienstatus {ms_val} – trotzdem gepostet (durch Telegram-Freigabe gedeckt)")

def find_instagram_block(content):
    """Sucht ersten Instagram-Feed-Block (ohne Format: Story), der noch nicht gepostet wurde."""
    pattern = r"## Instagram\s*\n(.*?)(?=\n## |\Z)"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(0)
        if "[GEPOSTET" in block:
            continue
        body = match.group(1)
        if not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", body):
            print("Instagram-Entwurf übersprungen (nicht freigegeben).")
            continue
        claim_token = os.environ.get("PUBLICATION_CLAIM_TOKEN", "")
        if not claim_token or f"Publication-Claim: IN_BEARBEITUNG {claim_token}" not in body:
            continue
        text_match = re.search(r"Text:\s*(.+?)(?=\n(?:Bild|Video|Bilder|Quelle|Medienstatus|Nutzungsrecht):|\Z)", body, re.DOTALL)
        image_match = re.search(r"Bild:\s*(\S+)", body)
        if text_match and image_match:
            check_media_status_warning(block)
            return text_match.group(1).strip(), image_match.group(1).strip(), block
    return None, None, None

def create_container(ig_user_id, token, image_url, caption):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media"
    r = requests.post(url, data={"image_url": image_url, "caption": caption, "access_token": token}, timeout=60)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Fehler Container: {r.text}")
    return None

def publish(ig_user_id, token, creation_id):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media_publish"
    r = requests.post(url, data={"creation_id": creation_id, "access_token": token}, timeout=60)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Fehler Publish: {r.text}")
    return None

def wait(creation_id, token, max_wait=60):
    url = f"https://graph.instagram.com/v23.0/{creation_id}"
    for _ in range(max_wait // 5):
        r = requests.get(url, params={"fields": "status_code", "access_token": token}, timeout=30)
        if r.status_code == 200:
            status = r.json().get("status_code")
            if status == "FINISHED":
                return True
            if status == "ERROR":
                return False
        time.sleep(5)
    return False

def mark_block(content, block, media_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_block = re.sub(
        r"^## Instagram(?:\s+\[[^\]]+\])?",
        f"## Instagram [GEPOSTET {timestamp} | ID: {media_id}]",
        block,
        count=1,
        flags=re.MULTILINE,
    )
    new_block = re.sub(
        r"(?mi)^Status:\s*FREIGEGEBEN\s*$",
        "Status: GEPOSTET",
        new_block,
    )
    new_block = re.sub(
        r"(?mi)^Publication-Claim:\s*IN_BEARBEITUNG[^\n]*\r?\n?",
        "",
        new_block,
    )
    return content.replace(block, new_block, 1)

if __name__ == "__main__":
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not token:
        print("Fehler: Secrets fehlen.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    text, image_file, block = find_instagram_block(content)
    if not text:
        print("Kein freigegebener Instagram-Beitrag gefunden.")
        exit(0)

    processed_image_file = process_image_for_instagram(image_file)
    image_url = asset_url(processed_image_file, REPO_RAW)
    print(f"Instagram-Beitrag gefunden – veröffentliche {processed_image_file}...")

    creation_id = create_container(ig_user_id, token, image_url, text)
    if not creation_id:
        exit(1)

    if not wait(creation_id, token):
        print("Verarbeitung fehlgeschlagen.")
        exit(1)

    post_id = publish(ig_user_id, token, creation_id)
    if post_id:
        print(f"Erfolgreich veröffentlicht: {post_id}")
        content = mark_block(content, block, post_id)
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Veröffentlichung fehlgeschlagen.")
