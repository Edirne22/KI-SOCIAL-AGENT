import os
import re
import time
import requests

from asset_paths import asset_url
from datetime import datetime

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"

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
    new_block = block.replace("## Instagram", f"## Instagram [GEPOSTET {timestamp} | ID: {media_id}]", 1)
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

    image_url = asset_url(image_file, REPO_RAW)
    print(f"Instagram-Beitrag gefunden – veröffentliche {image_file}...")

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
