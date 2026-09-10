import os
import re
import time
import requests

def parse_published_file():
    """Sucht gezielt den ersten Instagram-Story-Block mit Status FREIGEGEBEN."""
    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"^## Beitrag\s*$", content, flags=re.MULTILINE)

    for block in blocks:
        # Story erkennen: Plattform Instagram + Format: Story + Status FREIGEGEBEN
        if (re.search(r"Plattform:\s*Instagram", block)
                and re.search(r"Format:\s*Story", block)
                and re.search(r"Status:\s*FREIGEGEBEN", block)):

            text_match = re.search(r"Text:\s*(.*?)(?=\nBild-URL:|\Z)", block, re.DOTALL)
            post_text = text_match.group(1).strip() if text_match else ""

            url_match = re.search(r"Bild-URL:\s*(\S+)", block)
            image_url = url_match.group(1).strip() if url_match else None

            original_block = "## Beitrag" + block
            return post_text, image_url, original_block, content

    return None, None, None, content

def create_story_container(ig_user_id, access_token, image_url):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media"
    params = {
        "media_type": "STORIES",
        "image_url": image_url,
        "access_token": access_token
    }
    response = requests.post(url, data=params, timeout=60)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler beim Erstellen des Story-Containers: {response.text}")
    return None

def publish_media(ig_user_id, access_token, creation_id):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media_publish"
    params = {"creation_id": creation_id, "access_token": access_token}
    response = requests.post(url, data=params, timeout=60)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler beim Veröffentlichen der Story: {response.text}")
    return None

def wait_for_container(creation_id, access_token, max_wait=60):
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

def mark_as_published(content, original_block):
    new_block = original_block.replace("Status: FREIGEGEBEN", "Status: VERÖFFENTLICHT", 1)
    new_content = content.replace(original_block, new_block, 1)
    with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not access_token:
        print("Fehler: Instagram-Secrets fehlen.")
        exit(1)

    post_text, image_url, original_block, content = parse_published_file()

    if not original_block:
        print("Keine freigegebene Instagram-Story gefunden.")
        exit(0)

    if not image_url:
        print("Fehler: Story benötigt eine Bild-URL.")
        exit(1)

    print("Freigegebene Instagram-Story gefunden – veröffentliche jetzt...")

    creation_id = create_story_container(ig_user_id, access_token, image_url)
    if not creation_id:
        print("Story-Container-Erstellung fehlgeschlagen.")
        exit(1)

    print(f"Story-Container erstellt: {creation_id}. Warte auf Verarbeitung...")
    if not wait_for_container(creation_id, access_token):
        print("Story-Verarbeitung fehlgeschlagen.")
        exit(1)

    post_id = publish_media(ig_user_id, access_token, creation_id)
    if post_id:
        print(f"Story erfolgreich veröffentlicht mit ID: {post_id}")
        mark_as_published(content, original_block)
    else:
        print("Story-Veröffentlichung fehlgeschlagen.")
