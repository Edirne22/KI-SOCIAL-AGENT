"""Explicit /privat media intake; no vision inference or social dispatch."""
import re
import json
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import uuid
import requests
from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import new_manifest,store_original

MAX_DOWNLOAD=19*1024*1024
MAX_QUARANTINE_ITEMS=100
ALLOWED={"image/jpeg":"jpg","image/png":"png","video/mp4":"mp4","video/quicktime":"mov"}

class PermanentTelegramFileError(ValueError):
    """This Telegram file can never be downloaded by retrying the same getFile."""

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
    try:
        info=get("https://api.telegram.org/bot"+token+"/getFile",params={"file_id":file_id},timeout=25)
    except requests.RequestException:
        raise RuntimeError("Telegram-getFile Netzwerkfehler; erneuter Versuch erforderlich.") from None
    # Telegram's public Bot API may reject oversized videos directly in
    # getFile (HTTP 400) before returning file_size/file_path. Treat that as
    # a permanent per-item error, not as a retryable outage that blocks
    # every later update. Never log/propagate the raw requests URL: it
    # contains the bot token and may include a private Telegram file ID.
    status=getattr(info,"status_code",200)
    try:
        obj=info.json()
    except (ValueError,TypeError):
        obj={}
    if not isinstance(obj,dict):
        obj={}
    error_code=obj.get("error_code")
    if status in (400,413) or error_code in (400,413):
        description=str(obj.get("description") or "").lower()
        if (status==413 or error_code==413
                or any(text in description for text in
                       ("file is too big","file too big","file is too large",
                        "file too large","request entity too large"))):
            raise PermanentTelegramFileError("Telegram-Datei überschreitet das Bot-Downloadlimit; bitte Dashboard-Upload verwenden. Bereits gespeicherte Albumteile bleiben privat.")
        raise PermanentTelegramFileError("Telegram kann diese Datei nicht bereitstellen; Datei erneut senden oder Dashboard-Upload verwenden.")
    try:
        info.raise_for_status()
    except requests.HTTPError as exc:
        response=getattr(exc,"response",None)
        code=getattr(response,"status_code",status)
        # A non-permanent API error remains retryable without acknowledging
        # the update; bot token and file_id must never reach exception logs.
        raise RuntimeError("Telegram-getFile vorübergehend nicht verfügbar (HTTP "+str(code)+"); erneuter Versuch erforderlich.") from None
    result=obj.get("result") or {}
    if not obj.get("ok") or not result.get("file_path"):
        raise RuntimeError("Telegram-Datei nicht verfügbar")
    if result.get("file_size",0)>MAX_DOWNLOAD:
        raise PermanentTelegramFileError("Datei zu groß für den Telegram-Bot-Download; Dashboard-Upload verwenden.")
    path=result["file_path"]
    if not re.fullmatch(r"[a-zA-Z0-9_./-]{1,250}",path) or ".." in path.split("/"):
        raise ValueError("Ungültiger Telegram-Dateipfad")
    try:
        response=get("https://api.telegram.org/file/bot"+token+"/"+path,timeout=90,stream=True)
    except requests.RequestException:
        raise RuntimeError("Telegram-Dateidownload Netzwerkfehler; erneuter Versuch erforderlich.") from None
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        res=getattr(exc,"response",None)
        status=getattr(res,"status_code",getattr(response,"status_code","unknown"))
        if status in (400,413):
            raise PermanentTelegramFileError("Telegram-Datei über Bot nicht abrufbar; Dashboard-Upload verwenden.") from None
        raise RuntimeError("Telegram-Dateidownload HTTP "+str(status)+"; erneuter Versuch erforderlich.") from None
    buf=bytearray()
    try:
        for part in response.iter_content(chunk_size=65536):
            buf.extend(part)
            if len(buf)>MAX_DOWNLOAD:
                raise PermanentTelegramFileError("Datei zu groß; Dashboard-Upload verwenden.")
    except requests.RequestException:
        raise RuntimeError("Telegram-Dateidownload unterbrochen; erneuter Versuch erforderlich.") from None
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
    return ("Album-Datei zurückgehalten und bis zur privaten Freigabe vorgemerkt · "
            + manifest["job_id"] + " · Keine Veröffentlichung.")

def _reject_permanent(client, bucket, manifest, update_id, file_id):
    """Metadata-only audit marker. A failed Telegram download is NEVER an asset."""
    key=(manifest["prefix"]+"rejected/"+_asset_id(update_id,file_id)+".json")
    record={"schema":"PRIVATE-TELEGRAM-REJECTED-V1",
            "update_id":update_id,"reason":"getfile-permanent-rejection"}
    payload=json.dumps(record).encode("utf-8")
    try:
        client.put_object(Bucket=bucket,Key=key,Body=payload,
                          ContentType="application/json",IfNoneMatch="*")
    except Exception as exc:
        code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
        if code not in ("PreconditionFailed","412"):
            raise
        stored=client.get_object(Bucket=bucket,Key=key)["Body"].read()
        if stored!=payload:
            raise RuntimeError("Rejected item audit record collision") from None


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
        owner_hash = sha256(str((message.get("chat") or {}).get("id")).encode()).hexdigest()
        if (saved.get("job_id") != job_id or saved.get("lane") != "private"
                or (saved.get("owner_hash") is not None and saved["owner_hash"] != owner_hash)):
            raise RuntimeError("Album index identity mismatch")
        return new_manifest(lane="private", title="Privates Telegram-Album",
                            job_id=job_id, created_at=datetime.fromisoformat(saved["created_at"]))
    created = datetime.fromtimestamp(int(message["date"]), timezone.utc)
    candidate = new_manifest(lane="private", title="Privates Telegram-Album",
                             job_id=job_id, created_at=created)
    record = {"job_id": job_id, "lane": "private", "created_at": candidate["created_at"],
              "owner_hash": sha256(str((message.get("chat") or {}).get("id")).encode()).hexdigest()}
    try:
        client.put_object(Bucket=bucket, Key=index_key,
                          Body=json.dumps(record).encode("utf-8"),
                          ContentType="application/json", IfNoneMatch="*")
    except Exception as exc:
        code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
        if code not in ("PreconditionFailed", "412", "ConditionalRequestConflict", "409"):
            raise
        winner = json.loads(client.get_object(Bucket=bucket, Key=index_key)["Body"].read())
        owner_hash = sha256(str((message.get("chat") or {}).get("id")).encode()).hexdigest()
        if (winner.get("job_id") != job_id or winner.get("lane") != "private"
                or (winner.get("owner_hash") is not None and winner["owner_hash"] != owner_hash)):
            raise RuntimeError("Album index collision")
        return new_manifest(lane="private", title="Privates Telegram-Album",
                            job_id=job_id, created_at=datetime.fromisoformat(winner["created_at"]))
    return candidate


# A persisted authorization is distinct from the first media download. A
# captioned video may be permanently rejected by Telegram before any manifest
# exists; nevertheless the owner has explicitly authorized the *album*.
def _authorization_key(manifest):
    return manifest["prefix"] + "authorization.json"


def _authorized(client, bucket, manifest, chat):
    key = _authorization_key(manifest)
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except Exception as exc:
        if not _missing(exc):
            raise
        # Backwards-compatible: pre-upgrade manifests were only created by
        # successful owner-captioned media in the single authorized bot chat.
        return _read_manifest(client, bucket, manifest["prefix"] + "manifest.json") is not None
    record = json.loads(obj["Body"].read())
    if (record.get("schema") != "PRIVATE-TELEGRAM-ALBUM-AUTH-V1"
            or record.get("job_id") != manifest["job_id"]
            or record.get("owner_hash") != sha256(str(chat).encode()).hexdigest()):
        raise PermissionError("Album authorization identity mismatch")
    return True


def _authorize(client, bucket, manifest, chat):
    record = {"schema": "PRIVATE-TELEGRAM-ALBUM-AUTH-V1",
              "job_id": manifest["job_id"],
              "owner_hash": sha256(str(chat).encode()).hexdigest()}
    payload = json.dumps(record, sort_keys=True).encode("utf-8")
    key = _authorization_key(manifest)
    try:
        client.put_object(Bucket=bucket, Key=key, Body=payload,
                          ContentType="application/json", IfNoneMatch="*")
    except Exception as exc:
        code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
        if code not in ("PreconditionFailed", "412"):
            raise
        previous = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        if previous != payload:
            raise PermissionError("Album authorization collision") from None


def _replay(client, bucket, manifest, token, get):
    """Replay only an explicitly authorized album; keep transient errors retryable."""
    prefix = manifest["prefix"] + "quarantine/"
    marker = None
    stored_count = rejected_count = 0
    while True:
        args = {"Bucket": bucket, "Prefix": prefix}
        if marker:
            args["ContinuationToken"] = marker
        page = client.list_objects_v2(**args)
        for entry in page.get("Contents", []):
            item = json.loads(client.get_object(
                Bucket=bucket, Key=entry["Key"])["Body"].read())
            if (not isinstance(item.get("update_id"), int)
                    or not isinstance(item.get("file_id"), str)
                    or item.get("mime") not in ALLOWED):
                raise ValueError("Invalid quarantined album metadata")
            try:
                _commit(client, bucket, manifest, item["file_id"], item["mime"],
                        item["update_id"], token, get)
            except PermanentTelegramFileError:
                _reject_permanent(client, bucket, manifest,
                                  item["update_id"], item["file_id"])
                client.delete_object(Bucket=bucket, Key=entry["Key"])
                rejected_count += 1
                continue
            client.delete_object(Bucket=bucket, Key=entry["Key"])
            stored_count += 1
        marker = page.get("NextContinuationToken")
        if not marker:
            break
    return stored_count, rejected_count


def _rejected_count(client, bucket, manifest):
    """Read metadata only, including rejections recorded by earlier retries."""
    args = {"Bucket": bucket, "Prefix": manifest["prefix"] + "rejected/",
            "MaxKeys": 1000}
    page = client.list_objects_v2(**args)
    if page.get("IsTruncated") or page.get("NextContinuationToken"):
        raise RuntimeError("Zu viele abgewiesene Albumdateien; manuelle Prüfung erforderlich.")
    return len(page.get("Contents", []))


def _indexed_album(client, bucket, job_id, owner_chat):
    if not re.fullmatch(r"tgalbum[a-f0-9]{32}", job_id):
        raise ValueError("Ungültige private Album-ID.")
    index_key = "private/v1/telegram-album-index/" + job_id + ".json"
    try:
        obj = client.get_object(Bucket=bucket, Key=index_key)
    except Exception as exc:
        if _missing(exc):
            raise ValueError("Privates Album nicht gefunden.") from None
        raise
    item = json.loads(obj["Body"].read())
    if (item.get("job_id") != job_id or item.get("lane") != "private"
            or (item.get("owner_hash") is not None
                and item["owner_hash"] != sha256(str(owner_chat).encode()).hexdigest())):
        raise PermissionError("Privates Album nicht autorisiert.")
    created = datetime.fromisoformat(item["created_at"])
    if (created.tzinfo is None
            or created < datetime.now(timezone.utc) - timedelta(days=3)
            or created > datetime.now(timezone.utc) + timedelta(days=1)):
        raise ValueError("Album außerhalb des 72-Stunden-Wiederherstellungsfensters.")
    # Existing records without owner_hash originated in the earlier single
    # authorized-chat router; allow explicit owner recovery only for 72 hours.
    return new_manifest(lane="private", title="Privates Telegram-Album",
                        job_id=job_id, created_at=created)


def handle_private_command(text, *, chat, authorized_chat, token,
                           client=None, bucket=None, get=requests.get):
    """Owner-only explicit text commands; never publish or log media."""
    if authorized_chat is None or str(chat) != str(authorized_chat):
        raise PermissionError("Unauthorized private media chat")
    normalized = " ".join(str(text).strip().lower().split())
    if client is None:
        client, bucket = client_from_env()
    if not bucket:
        raise ValueError("R2-Bucket fehlt")
    if normalized == "/privat sammeln":
        prefix = "private/v1/telegram-album-index/"
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        albums = []
        page = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        if page.get("IsTruncated"):
            raise RuntimeError("Zu viele private Album-Indizes; Sammlung bitte manuell eingrenzen.")
        for entry in page.get("Contents", []):
            job_id = entry["Key"][len(prefix):].removesuffix(".json")
            if not re.fullmatch(r"tgalbum[a-f0-9]{32}", job_id):
                continue
            try:
                manifest = _indexed_album(client, bucket, job_id, chat)
            except (ValueError, PermissionError):
                continue
            created = datetime.fromisoformat(manifest["created_at"])
            stored = _read_manifest(client, bucket, manifest["prefix"] + "manifest.json")
            if created >= cutoff and stored and stored.get("assets"):
                albums.append({"job_id": job_id, "created_at": manifest["created_at"],
                               "asset_count": len(stored["assets"]), "prefix": manifest["prefix"]})
        if not albums:
            return "Keine privaten Telegram-Alben der letzten 6 Stunden zum Sammeln gefunden."
        albums.sort(key=lambda item: (item["created_at"], item["job_id"]))
        digest = sha256("|".join(item["job_id"] for item in albums).encode()).hexdigest()[:24]
        collection_id = "tgcollection" + digest
        record = {"schema": "PRIVATE-TELEGRAM-COLLECTION-V1", "collection_id": collection_id,
                  "lane": "private", "created_at": datetime.now(timezone.utc).isoformat(),
                  "albums": albums, "asset_count": sum(item["asset_count"] for item in albums),
                  "publish_allowed": False}
        key = "private/v1/collections/" + collection_id + "/manifest.json"
        client.put_object(Bucket=bucket, Key=key,
                          Body=json.dumps(record, ensure_ascii=False).encode("utf-8"),
                          ContentType="application/json")
        return ("Private Sammlung erstellt · " + collection_id + " · "
                + str(record["asset_count"]) + " Medien aus " + str(len(albums))
                + " Alben · Keine Veröffentlichung.")
    if normalized == "/privat" or normalized == "/privat neu":
        return ("Album mit /privat als Beschriftung senden. "
                "Vorgemerkte Alben: /privat offene")
    if normalized == "/privat offene":
        prefix = "private/v1/telegram-album-index/"
        results = []
        marker = None
        scanned = 0
        while True:
            args = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
            if marker:
                args["ContinuationToken"] = marker
            page = client.list_objects_v2(**args)
            for entry in page.get("Contents", []):
                scanned += 1
                if scanned > 5000:
                    raise RuntimeError("Zu viele private Album-Indizes; manuelle Prüfung erforderlich.")
                job_id = entry["Key"][len(prefix):].removesuffix(".json")
                if not re.fullmatch(r"tgalbum[a-f0-9]{32}", job_id):
                    continue
                try:
                    manifest = _indexed_album(client, bucket, job_id, chat)
                except (ValueError, PermissionError):
                    continue
                pending = client.list_objects_v2(
                    Bucket=bucket, Prefix=manifest["prefix"] + "quarantine/", MaxKeys=100)
                count = len(pending.get("Contents", []))
                rejected = _rejected_count(client, bucket, manifest)
                if count or rejected:
                    results.append((int(count > 0), manifest["created_at"],
                                    job_id, count, rejected))
            marker = page.get("NextContinuationToken")
            if not marker:
                break
        if not results:
            return "Keine vorgemerkten privaten Alben aus den letzten 72 Stunden."
        results.sort(reverse=True)
        selected = results[:5]
        return ("Private Alben aus den letzten 72 Stunden (nur Metadaten):\\n"
                + "\\n".join(job_id + " · " + str(count) + " vorgemerkt, "
                            + str(rejected) + " abgewiesen"
                            for _, _, job_id, count, rejected in selected)
                + "\\nVorgemerkte Dateien gezielt freigeben: /privat freigeben tgalbum...")
    match = re.fullmatch(r"/privat freigeben (tgalbum[a-f0-9]{32})", normalized)
    if not match:
        raise ValueError("Bitte /privat offene oder /privat freigeben tgalbum... verwenden.")
    manifest = _indexed_album(client, bucket, match.group(1), chat)
    pending = client.list_objects_v2(
        Bucket=bucket, Prefix=manifest["prefix"] + "quarantine/", MaxKeys=1)
    if not pending.get("Contents"):
        return ("Keine vorgemerkten Dateien für " + manifest["job_id"]
                + " vorhanden; " + str(_rejected_count(client, bucket, manifest))
                + " Datei(en) von Telegram abgewiesen. "
                + "Bereits gespeicherte Dateien bleiben privat.")
    _authorize(client, bucket, manifest, chat)
    stored, rejected = _replay(client, bucket, manifest, token, get)
    return ("Privates Album " + manifest["job_id"] + ": "
            + str(stored) + " vorgemerkte Datei(en) in R2 übernommen; "
            + str(_rejected_count(client, bucket, manifest))
            + " Datei(en) insgesamt von Telegram abgewiesen. "
            + "Keine Veröffentlichung.")


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
        if identified is None:
            doc = message.get("document") or message.get("video") or {}
            photos = message.get("photo") or []
            if not photos and (not doc.get("file_id") or doc.get("mime_type") not in ALLOWED):
                raise ValueError("Unsupported uncaptioned album item")
        job_id = "tgalbum" + sha256((str(chat) + ":" + str(group)).encode()).hexdigest()[:32]
        manifest = _album_manifest(client, bucket, job_id, message)
    else:
        job_id = "tg" + str(update_id).zfill(12)
        manifest = new_manifest(lane="private", title="Privater Telegram-Medieneingang",
                                job_id=job_id)
    key = manifest["prefix"] + "manifest.json"
    if group and identified is not None:
        # Persist the owner's explicit album authorization before attempting
        # the leading download (which may fail on a large Telegram video).
        _authorize(client, bucket, manifest, chat)
    if identified is None:
        if not _authorized(client, bucket, manifest, chat):
            return _quarantine(client, bucket, manifest, message, update_id)
        continuation = dict(message, caption="/privat")
        identified = identify(continuation)
    file_id, mime, extension = identified
    if not file_id:
        raise ValueError("Telegram-Datei-ID fehlt")
    previously = _read_manifest(client, bucket, key)
    duplicate = bool(previously and any(a["asset_id"] == _asset_id(update_id, file_id)
                                         for a in previously.get("assets", [])))
    try:
        _commit(client, bucket, manifest, file_id, mime, update_id, token, get)
    except PermanentTelegramFileError as exc:
        if not group:
            raise
        _reject_permanent(client, bucket, manifest, update_id, file_id)
        # Although the captioned media itself was rejected, the owner already
        # authorized the album. Salvage valid earlier quarantine items.
        recovered, other_rejected = _replay(client, bucket, manifest, token, get)
        return (str(exc) + " · " + str(recovered)
                + " vorgemerkte Albumdatei(en) privat gespeichert; "
                + str(other_rejected + 1) + " Datei(en) abgewiesen. "
                + "Album-ID: " + job_id)
    # Replay earlier metadata-only quarantine items after explicit authority.
    recovered, rejected_count = _replay(client, bucket, manifest, token, get) if group else (0, 0)
    warning = (" · "+str(rejected_count)+" frühere Albumdatei(en) von Telegram dauerhaft abgewiesen; separat über Dashboard hochladen."
               if rejected_count else "")
    if duplicate:
        return "Privater Upload bereits gespeichert · " + job_id + warning
    return "Privat in R2 gespeichert · " + job_id + " · Keine Veröffentlichung." + warning
