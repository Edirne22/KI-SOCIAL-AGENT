import os
import re
import mimetypes
import requests
from datetime import datetime

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".3gp", ".avi", ".mkv", ".webm"}


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


def find_facebook_block(content):
    """Sucht den ersten freigegebenen, reservierten Facebook-Block."""
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

        text_match = re.search(
            r"Text:\s*(.+?)(?=\n(?:Bild|Video|Bilder|Quelle|Medienstatus|Nutzungsrecht|Musik|Poster|Link-Preview):|\Z)",
            body,
            re.DOTALL,
        )
        image_match = re.search(r"(?mi)^Bild:\s*(?!auto\s*$)(\S+)", body)
        video_match = re.search(r"(?mi)^Video:\s*(?!auto\s*$)(\S+)", body)
        source_match = re.search(r"(?mi)^Quelle:\s*(https?://\S+)", body)
        link_preview = bool(re.search(r"(?mi)^Link-Preview:\s*offiziell\s*$", body))

        if text_match:
            message = text_match.group(1).strip()
            source_url = source_match.group(1) if source_match else None

            # Bei offizieller Link-Preview wird die Quelle als echter Facebook-Link
            # übergeben statt als zusätzliche sichtbare Quelle-Zeile. So kann Meta
            # die Open-Graph-Vorschau der Originalseite erzeugen.
            if source_url and not link_preview:
                message += f"\n\nQuelle: {source_url}"

            check_media_status_warning(block)
            return (
                message,
                image_match.group(1) if image_match else None,
                video_match.group(1) if video_match else None,
                source_url if link_preview else None,
                block,
            )
    return None, None, None, None, None


def _video_mime(path):
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "video/mp4"


def post_video_to_facebook(page_id, page_token, message, video_file):
    """Lädt ein lokales Repo-Video direkt zu Facebook hoch."""
    if not os.path.isfile(video_file):
        print(f"Fehler: Video-Datei nicht gefunden: {video_file}")
        return None

    extension = os.path.splitext(video_file)[1].lower()
    if extension not in VIDEO_EXTENSIONS:
        print(f"Fehler: Nicht unterstütztes Videoformat: {extension or 'ohne Endung'}")
        return None

    url = f"https://graph-video.facebook.com/v26.0/{page_id}/videos"
    payload = {"description": message, "access_token": page_token}

    try:
        with open(video_file, "rb") as handle:
            files = {"source": (os.path.basename(video_file), handle, _video_mime(video_file))}
            response = requests.post(url, data=payload, files=files, timeout=300)
    except OSError as exc:
        print(f"Fehler beim Lesen der Video-Datei: {exc}")
        return None
    except requests.RequestException as exc:
        print(f"Fehler beim Facebook-Video-Upload: {exc}")
        return None

    if response.status_code == 200:
        video_id = response.json().get("id")
        if video_id:
            print(f"Facebook-Video erfolgreich hochgeladen: {video_id}")
            return video_id
        print(f"Fehler: Facebook meldet Erfolg, aber keine Video-ID: {response.text}")
        return None

    print(f"Fehler beim Facebook-Video-Upload: {response.status_code} {response.text}")
    return None


def post_to_facebook(page_id, page_token, message, image_file=None, video_file=None, link_url=None):
    # Video hat Vorrang, danach explizites Bild. Link-Preview gilt fuer Text/Link-Posts.
    if video_file:
        return post_video_to_facebook(page_id, page_token, message, video_file)

    if image_file:
        from asset_paths import asset_url
        url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
        payload = {
            "url": asset_url(image_file, REPO_RAW),
            "caption": message,
            "access_token": page_token,
        }
    else:
        url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
        payload = {"message": message, "access_token": page_token}
        if link_url:
            payload["link"] = link_url
            print(f"Facebook-Link-Preview angefordert: {link_url}")

    try:
        response = requests.post(url, data=payload, timeout=30)
    except requests.RequestException as exc:
        print(f"Fehler beim Facebook-Post: {exc}")
        return None

    if response.status_code == 200:
        return response.json().get("id")
    print(f"Fehler: {response.text}")
    return None


def mark_block(content, block, post_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_block = re.sub(
        r"^## Facebook(?:\s+\[[^\]]+\])?",
        f"## Facebook [GEPOSTET {timestamp} | ID: {post_id}]",
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
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN")

    if not page_id or not page_token:
        print("Fehler: Secrets fehlen.")
        exit(1)

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as f:
        content = f.read()

    text, image_file, video_file, link_url, block = find_facebook_block(content)
    if not text:
        print("Kein freigegebener Facebook-Beitrag gefunden.")
        exit(0)

    media_type = "Video" if video_file else "Bild" if image_file else "Link" if link_url else "Text"
    print(f"Facebook-Beitrag gefunden – veröffentliche jetzt als {media_type}...")
    post_id = post_to_facebook(page_id, page_token, text, image_file, video_file, link_url)

    if post_id:
        print(f"Erfolgreich veröffentlicht: {post_id}")
        content = mark_block(content, block, post_id)
        with open("content/PUBLISHED.md", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Veröffentlichung fehlgeschlagen – Block wird NICHT als GEPOSTET markiert.")
        exit(1)
