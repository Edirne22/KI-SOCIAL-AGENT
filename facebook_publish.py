import os
import re
import requests
from datetime import datetime

def parse_published_file():
    """Liest die PUBLISHED.md und sucht nach einem freigegebenen Beitrag."""
    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Suche nach dem ersten Block mit Status FREIGEGEBEN
    pattern = r"(## Beitrag.*?Status: FREIGEGEBEN.*?)(?=## Beitrag|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None, content

    block = match.group(1)
    # Extrahiere den Text nach "Text:"
    text_match = re.search(r"Text:\s*(.*?)(?=\n##|\Z)", block, re.DOTALL)
    if not text_match:
        return None, content

    post_text = text_match.group(1).strip()
    return post_text, content

def post_to_facebook(page_id, page_token, message):
    url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
    params = {
        "message": message,
        "access_token": page_token
    }
    response = requests.post(url, data=params, timeout=30)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"Fehler beim Posten: {response.text}")
        return None

def mark_as_published(content, block_start_marker):
    """Markiert den Block als VERÖFFENTLICHT."""
    new_content = content.replace("Status: FREIGEGEBEN", "Status: VERÖFFENTLICHT", 1)
    with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN")

    if not page_id or not page_token:
        print("Fehler: Facebook-Secrets fehlen.")
        exit(1)

    post_text, content = parse_published_file()
    if not post_text:
        print("Kein freigegebener Beitrag gefunden.")
        exit(0)

    print("Freigegebenen Beitrag gefunden – veröffentliche jetzt...")
    post_id = post_to_facebook(page_id, page_token, post_text)

    if post_id:
        print(f"Erfolgreich veröffentlicht mit ID: {post_id}")
        mark_as_published(content, None)
    else:
        print("Veröffentlichung fehlgeschlagen.")
