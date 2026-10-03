"""Explicit /privat media intake; no vision inference or social dispatch."""
import re
import json
from datetime import datetime, timezone
from hashlib import sha256
import uuid
import requests
from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import new_manifest,store_original

MAX_DOWNLOAD=19*1024*1024
MAX_QUARANTINE_ITEMS=100
ALLOWED={"image/jpeg":"jpg","image/png":"png","video/mp4":"mp4","video/quicktime":"mov"}

def identify(message):
    caption=str(message.get("caption") or "").strip().lower()
    if caption not in ("/privat","/privat neu"):
        return None
    doc=message.get("document") or message.get("video") or {}
    photos=message.get("photo") or []
    if photos:
        return photos[-1].get("file_id"),"image/jpeg","jpg"
    mime=doc.get("mime_type")
    if mime in ALLOWED:
        return doc.get("file_id"),mime,ALLOWED[mime]
    raise ValueError("Bitte ein unterstütztes Foto oder Video mit /privat senden.")

def download(file_id,token,get=requests.get):
    if not token or not file_id:
        raise ValueError("Telegram-Datei fehlt")
    info=get("https://api.telegram.org/bot"+token+"/getFile",params={"file_id":file_id},timeout=25)
    info.raise_for_status()
    obj=info.json()
    result=obj.get("result") or {}
    if not obj.get("ok") or not result.get("file_path"):
        raise RuntimeError("Telegram-Datei nicht verfügbar")
    if result.get("file_size",0)>MAX_DOWNLOAD:
        raise ValueError("Datei zu groß für den Telegram-Bot-Download; Dashboard-Upload verwenden.")
    path=result["file_path"]
    if not re.fullmatch(r"[a-zA-Z0-9_./-]{1,250}",path) or ".." in path.split("/"):
        raise ValueError("Ungültiger Telegram-Dateipfad")
    response=get("https://api.telegram.org/file/bot"+token+"/"+path,timeout=90,stream=True)
    response.raise_for_status()
    buf=bytearray()
    for part in response.iter_content(chunk_size=65536):
        buf.extend(part)
        if len(buf)>MAX_DOWNLOAD:
            raise ValueError("Datei zu groß; Dashboard-Upload verwenden.")
    return bytes(buf)

def _missing(exc):
    return str(getattr(exc, "response", {}).get("Error", {}).get("Code", "")) in ("404", "NoSuchKey", "NotFound")

def _asset_id(update_id, file_id):
    return "file" + uuid.uuid5(uuid.NAMESPACE_URL, str(update_id) + ":" + file_id).hex

def _read_manifest(client, bucket, key):
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except Exception as exc:
        if _missing(exc):
            return None
        raise
    return json.loads(obj["Body"].read())

def _quarantine(client, bucket, manifest, message, update_id):
    # Metadata only: no unauthorized media bytes and no token stored.
    doc = message.get("document") or message.get("video") or {}
    photos = message.get("photo") or []
    file_id = photos[-1].get("file_id") if photos else doc.get("file_id")
    mime = "image/jpeg" if photos else doc.get("mime_type")
    if not file_id or mime not in ALLOWED:
        raise ValueError("Unsupported uncaptioned album item")
    prefix = manifest["prefix"] + "quarantine/"
    key = prefix + _asset_id(update_id, file_id) + ".json"
    # Fail closed before creating unbounded pending album records.
    count = 0
    marker = None
    already_present = False
    while True:
        args = {"Bucket": bucket, "Prefix": prefix}
        if marker:
            args["ContinuationToken"] = marker
        page = client.list_objects_v2(**args)
        for entry in page.get("Contents", []):
            count += 1
            already_present |= entry["Key"] == key
        marker = page.get("NextContinuationToken")
        if not marker:
            break
    if count >= MAX_QUARANTINE_ITEMS and not already_present:
        raise ValueError("Album quarantine limit reached")
    item = {"update_id": update_id, "file_id": file_id, "mime": mime}
    try:
        client.put_object(Bucket=bucket, Key=key, Body=json.dumps(item).encode(),
                          ContentType="application/json", IfNoneMatch="*")
    except Exception as exc:
        code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
        if code not in ("PreconditionFailed", "412"):
            raise
        previous = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())
        if previous != item:
            raise RuntimeError("Quarantine collision")
    return "Album-Datei zurückgehalten und bis zur privaten Freigabe dauerhaft vorgemerkt."

def _commit(client, bucket, manifest, file_id, mime, update_id, token, get):
    asset_id = _asset_id(update_id, file_id)
    key = manifest["prefix"] + "manifest.json"
    for attempt in range(5):
        saved = _read_manifest(client, bucket, key)
        if saved:
            if any(a["asset_id"] == asset_id for a in saved.get("assets", [])):
                return saved
            manifest = saved
        payload = download(file_id, token, get=get)
        try:
            return store_original(client, bucket, manifest, asset_id=asset_id,
                                  filename=asset_id + "." + ALLOWED[mime],
                                  mime=mime, payload=payload)
        except Exception as exc:
            code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
            if code not in ("PreconditionFailed", "412", "ConditionalRequestConflict", "409"):
                # The warehouse may reject stale manifests before conditional put.
                if "manifest changed concurrently" not in str(exc):
                    raise
    raise RuntimeError("Concurrent album update; retry Telegram event")

def _album_manifest(client, bucket, job_id, message):
    # Stable index avoids splitting an album when Telegram items cross UTC midnight.
    # Store only private job metadata; never put media or authorization in the index.
    index_key = "private/v1/telegram-album-index/" + job_id + ".json"
    try:
        obj = client.get_object(Bucket=bucket, Key=index_key)
    except Exception as exc:
        if not _missing(exc):
            raise
        obj = None
    if obj is not None:
        saved = json.loads(obj["Body"].read())
        if saved.get("job_id") != job_id or saved.get("lane") != "private":
            raise RuntimeError("Album index identity mismatch")
        return new_manifest(lane="private", title="Privates Telegram-Album",
                            job_id=job_id, created_at=datetime.fromisoformat(saved["created_at"]))
    created = datetime.fromtimestamp(int(message["date"]), timezone.utc)
    candidate = new_manifest(lane="private", title="Privates Telegram-Album",
                             job_id=job_id, created_at=created)
    record = {"job_id": job_id, "lane": "private", "created_at": candidate["created_at"]}
    try:
        client.put_object(Bucket=bucket, Key=index_key,
                          Body=json.dumps(record).encode("utf-8"),
                          ContentType="application/json", IfNoneMatch="*")
    except Exception as exc:
        code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
        if code not in ("PreconditionFailed", "412", "ConditionalRequestConflict", "409"):
            raise
        winner = json.loads(client.get_object(Bucket=bucket, Key=index_key)["Body"].read())
        if winner.get("job_id") != job_id or winner.get("lane") != "private":
            raise RuntimeError("Album index collision")
        return new_manifest(lane="private", title="Privates Telegram-Album",
                            job_id=job_id, created_at=datetime.fromisoformat(winner["created_at"]))
    return candidate

def receive(message, *, update_id, token, client=None, bucket=None,
            get=requests.get, authorized_chat=None):
    group = message.get("media_group_id")
    chat = (message.get("chat") or {}).get("id")
    if authorized_chat is not None and str(chat) != str(authorized_chat):
        raise PermissionError("Unauthorized private media chat")
    identified = identify(message)
    if identified is None and not group:
        return None
    if client is None:
        client, bucket = client_from_env()
    if not bucket:
        raise ValueError("R2-Bucket fehlt")
    if group:
        if chat is None or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", str(group)):
            raise ValueError("Invalid album identity")
        job_id = "tgalbum" + sha256((str(chat) + ":" + str(group)).encode()).hexdigest()[:32]
        manifest = _album_manifest(client, bucket, job_id, message)
    else:
        job_id = "tg" + str(update_id).zfill(12)
        manifest = new_manifest(lane="private", title="Privater Telegram-Medieneingang",
                                job_id=job_id)
    key = manifest["prefix"] + "manifest.json"
    if identified is None:
        if not _read_manifest(client, bucket, key):
            return _quarantine(client, bucket, manifest, message, update_id)
        continuation = dict(message, caption="/privat")
        identified = identify(continuation)
    file_id, mime, extension = identified
    if not file_id:
        raise ValueError("Telegram-Datei-ID fehlt")
    previously = _read_manifest(client, bucket, key)
    duplicate = bool(previously and any(a["asset_id"] == _asset_id(update_id, file_id)
                                         for a in previously.get("assets", [])))
    _commit(client, bucket, manifest, file_id, mime, update_id, token, get)
    # Once owner explicitly authorizes the album, replay earlier uncaptioned items.
    # A failed replay leaves the durable record for a subsequent authorized retry.
    if group:
        prefix = manifest["prefix"] + "quarantine/"
        marker = None
        while True:
            args = {"Bucket": bucket, "Prefix": prefix}
            if marker:
                args["ContinuationToken"] = marker
            page = client.list_objects_v2(**args)
            for entry in page.get("Contents", []):
                item = json.loads(client.get_object(Bucket=bucket, Key=entry["Key"])["Body"].read())
                if item["mime"] not in ALLOWED:
                    raise ValueError("Invalid quarantined MIME")
                _commit(client, bucket, manifest, item["file_id"], item["mime"],
                        item["update_id"], token, get)
                client.delete_object(Bucket=bucket, Key=entry["Key"])
            marker = page.get("NextContinuationToken")
            if not marker:
                break
    if duplicate:
        return "Privater Upload bereits gespeichert · " + job_id
    return "Privat in R2 gespeichert · " + job_id + " · Keine Veröffentlichung."
