import os
import re
import time
import requests
from datetime import datetime

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"

def find_story_block(content):
    pattern = r"## Story\s*\n(.*?)(?=\n## |\Z)"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(0)
        if "[GEPOSTET" in block:
            continue
        body = match.group(1)
        bild_match = re.search(r"Bild:\s*(\S+)", body)
        video_match = re.search(r"Video:\s*(\S+)", body)
        if bild_match:
            return "image", bild_match.group(1).strip(), block
        if video_match:
            return "video", video_match.group(1).strip(), block
    return None, None, None

def create_story_image(ig_user_id, token, image_url):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media"
    r = requests.post(url, data={"media_type": "STORIES", "image_url": image_url, "access_token": token}, timeout=60)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Fehler: {r.text}")
    return None

def create_story_video(ig_user_id, token, video_url):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media"
    r = requests.post(url, data={"media_type": "STORIES", "video_url": video_url, "access_token": token}, timeout=60)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Fehler: {r.text}")
    return None

def publish(ig_user_id, token, creation_id):
    url = f"https://graph.instagram.com/v23.0/{ig_user_id}/media_publish"
    r = requests.post(url, data={"creation_id": creation_id, "access_token": token}, timeout=60)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Fehler: {r.text}")
    return None

def wait(creation_id, token, max_wait=180):
    url = f"https://graph.instagram.com/v23.0/{creation_id}"
    for _ in range(max_wait // 5):
        r = requests.get(url, params={"fields": "status_code", "access_token": token}, timeout=30)
        if r.status_code == 200:
            s = r.json().get("status_code")
            if s == "FINISHED":
                return True
            if s == "ERROR":
                return False
        time.sleep(5)
    return False

def mark_block(content, block, media_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_block = block.replace("## Story", f"## Story [GEPOSTET {timestamp} | ID: {media_id}]", 1)
    return content.replace(block, new_block, 1)

if __name__ == "__main__":
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not token:
        print("Fehler: Secrets fehlen.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    media_type, filename, block = find_story_block(content)
    if not filename:
        print("Keine freigegebene Story gefunden.")
        exit(0)

    file_url = REPO_RAW + filename
    print(f"Story gefunden ({media_type}): {filename}")

    if media_type == "video":
        creation_id = create_story_video(ig_user_id, token, file_url)
    else:
        creation_id = create_story_image(ig_user_id, token, file_url)

    if not creation_id:
        print("Story-Container-Erstellung fehlgeschlagen.")
        exit(1)

    print(f"Container: {creation_id}. Warte auf Verarbeitung...")
    if not wait(creation_id, token):
        print("Verarbeitung fehlgeschlagen.")
        exit(1)

    post_id = publish(ig_user_id, token, creation_id)
    if post_id:
        print(f"Story online: {post_id}")
        content = mark_block(content, block, post_id)
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Veröffentlichung fehlgeschlagen.")
