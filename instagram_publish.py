import os
import re
import time
import requests
from datetime import datetime

def parse_published_file():
    """Liest die PUBLISHED.md und sucht nach einem freigegebenen Instagram-Beitrag."""
    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Suche nach Block mit Plattform Instagram und Status FREIGEGEBEN
    pattern = r"(## Beitrag.*?Plattform:\s*Instagram.*?Status:\s*FREIGEGEBEN.*?)(?=## Beitrag|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None, None, None, content

    block = match.group(1)

    # Text extrahieren
    text_match = re.search(r"Text:\s*(.*?)(?=\nBild-URL:|\n##|\Z)", block, re.DOTALL)
    post_text = text_match.group(1).strip() if text_match else ""

    # Bild-URL extrahieren
    url_match = re.search(r"Bild-URL:\s*(\S+)", block)
    image_url = url_match.group(1).strip() if url_match else None

    return post_text, image_url, block, content

def create_media_container(ig_user_id, access_token, image_url, caption):
    """Erstellt einen Medien-Container für das Bild."""
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    response = requests.post(url, data=params, timeout=60)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler beim Erstellen des Containers: {response.text}")
    return None

def publish_media(ig_user_id, access_token, creation_id):
    """Veröffentlicht den erstellten Medien-Container."""
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    response = requests.post(url, data=params, timeout=60)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler beim Veröffentlichen: {response.text}")
    return None

def wait_for_container(creation_id, access_token, max_wait=60):
    """Wartet, bis der Container fertig verarbeitet ist."""
    url = f"https://graph.instagram.com/v23.0/{creation_id}"
    params = {"fields": "status_code", "access_token": access_token}
    for _ in range(max_wait // 5):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            status = response.json().get("status_code")
            if status == "FINISHED":
                return True
            if status == "ERROR":
                return False
        time.sleep(5)
    return False

def mark_as_published(content):
    new_content = content.replace("Status: FREIGEGEBEN", "Status: VERÖFFENTLICHT", 1)
    with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not access_token:
        print("Fehler: Instagram-Secrets fehlen.")
        exit(1)

    post_text, image_url, block, content = parse_published_file()

    if not post_text and not image_url:
        print("Kein freigegebener Instagram-Beitrag gefunden.")
        exit(0)

    if not image_url:
        print("Fehler: Instagram benötigt eine Bild-URL.")
        exit(1)

    print("Freigegebenen Instagram-Beitrag gefunden – veröffentliche jetzt...")

    creation_id = create_media_container(ig_user_id, access_token, image_url, post_text)
    if not creation_id:
        print("Container-Erstellung fehlgeschlagen.")
        exit(1)

    print(f"Container erstellt: {creation_id}. Warte auf Verarbeitung...")
    if not wait_for_container(creation_id, access_token):
        print("Container-Verarbeitung fehlgeschlagen.")
        exit(1)

    post_id = publish_media(ig_user_id, access_token, creation_id)
    if post_id:
        print(f"Erfolgreich veröffentlicht mit ID: {post_id}")
        mark_as_published(content)
    else:
        print("Veröffentlichung fehlgeschlagen.")
