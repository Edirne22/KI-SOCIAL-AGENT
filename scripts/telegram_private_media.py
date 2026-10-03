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

def receive(message,*,update_id,token,client=None,bucket=None,get=requests.get):
    identified=identify(message)
    if identified is None:return None
    file_id,mime,extension=identified
    if not file_id:raise ValueError("Telegram-Datei-ID fehlt")
    if client is None:client,bucket=client_from_env()
    if not bucket:raise ValueError("R2-Bucket fehlt")
    # Stable job per Telegram update: a retried event cannot create a second job.
    job_id="tg"+str(update_id).zfill(12)
    manifest=new_manifest(lane="private",title="Privater Telegram-Medieneingang",job_id=job_id)
    payload=download(file_id,token,get=get)
    key=manifest["prefix"]+"manifest.json"
    # A retry must not duplicate or overwrite originals.
    try:
        existing=client.get_object(Bucket=bucket,Key=key)
        if existing:
            return "Privater Upload bereits gespeichert · "+job_id
    except Exception as exc:
        code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
        if code not in ("404","NoSuchKey","NotFound"):raise
    asset_id="file"+uuid.uuid5(uuid.NAMESPACE_URL,str(update_id)+":"+file_id).hex
    store_original(client,bucket,manifest,asset_id=asset_id,filename=asset_id+"."+extension,
                   mime=mime,payload=payload)
    return "Privat in R2 gespeichert · "+job_id+" · Noch keine Verarbeitung oder Veröffentlichung."
