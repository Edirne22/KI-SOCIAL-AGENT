import os
import re
import requests
from datetime import datetime

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"

def find_facebook_block(content):
    """Sucht ersten Facebook-Block, der noch nicht gepostet wurde."""
    pattern = r"## Facebook\s*\n(.*?)(?=\n## |\Z)"
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(0)
        if "[GEPOSTET" in block:
            continue
        body = match.group(1)
        if not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", body):
            print("Facebook-Entwurf übersprungen (nicht freigegeben).")
            continue
        claim_token = os.environ.get("PUBLICATION_CLAIM_TOKEN", "")
        if not claim_token or f"Publication-Claim: IN_BEARBEITUNG {claim_token}" not in body:
            continue
        text_match = re.search(r"Text:\s*(.+?)(?=\nBild:|\Z)", body, re.DOTALL)
        if text_match:
            return text_match.group(1).strip(), block
    return None, None

def post_to_facebook(page_id, page_token, message):
    url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
    response = requests.post(url, data={"message": message, "access_token": page_token}, timeout=30)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler: {response.text}")
    return None

def mark_block(content, block, post_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_header = f"## Facebook [GEPOSTET {timestamp} | ID: {post_id}]"
    new_block = block.replace("## Facebook", new_header, 1)
    return content.replace(block, new_block, 1)

if __name__ == "__main__":
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN")

    if not page_id or not page_token:
        print("Fehler: Secrets fehlen.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    text, block = find_facebook_block(content)
    if not text:
        print("Kein freigegebener Facebook-Beitrag gefunden.")
        exit(0)

    print("Facebook-Beitrag gefunden – veröffentliche jetzt...")
    post_id = post_to_facebook(page_id, page_token, text)

    if post_id:
        print(f"Erfolgreich veröffentlicht: {post_id}")
        content = mark_block(content, block, post_id)
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Veröffentlichung fehlgeschlagen.")
