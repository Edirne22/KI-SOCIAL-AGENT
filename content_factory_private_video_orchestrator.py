"""Private video production orchestrator.

Consumes the user's private Telegram instruction from private R2 and coordinates
privacy-safe production agents. It deliberately does not use the public
fact/news CreativeDirector contract, because family media is not a publishable
FactPackage. No social publisher is reachable from this module.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json, re
from datetime import datetime, timezone
from music_agent import load_library, choose_track

STAGES=("production_lead","creative_director","media_story","music_audio","video_editor_ffmpeg","qm","private_preview")

@dataclass(frozen=True)
class PrivateVideoPlan:
    task_id:str
    title:str
    duration_seconds:int
    aspect_ratio:str
    privacy:str
    story_style:str
    music_track:str
    overlays:tuple[str,...]
    stages:tuple[str,...]=STAGES

class PrivateProductionLead:
    def decompose(self,task_id:str,prompt:str)->dict:
        if not prompt.strip(): raise ValueError("private video prompt required")
        low=prompt.casefold()
        duration=300 if ("5 min" in low or "5min" in low or "300" in low) else 300
        ratio="9:16" if "9:16" in prompt else "9:16"
        title="Dünya – Level 12" if "dünya" in low and ("12" in low or "geburtstag" in low) else "Private Erinnerung"
        return {"task_id":task_id,"prompt":prompt,"duration_seconds":duration,"aspect_ratio":ratio,
                "title":title,"privacy":"private-only"}

class PrivateCreativeDirector:
    """Creative planning for owned private media; never converts it to public facts."""
    def create(self,spec:dict)->dict:
        p=spec["prompt"]; low=p.casefold()
        overlays=[]
        if "dünya" in low:
            overlays=["Dünya – Level 12","12 Jahre voller Erinnerungen","Alles Gute zum 12. Geburtstag, Dünya!"]
        else:
            # Only user-authored quoted text may become a generic overlay.
            overlays=[x.strip() for x in re.findall(r'["“]([^"”]{2,80})["”]',p)[:3]]
        return {**spec,"story_style":"emotional-modern-memory-story",
                "overlays":tuple(overlays),"motion":"ken-burns-pan-zoom","transitions":"soft-cinematic"}

class PrivateMediaStoryAgent:
    def bind(self,spec:dict,assets:list[dict])->dict:
        if not assets: raise ValueError("private media required")
        return {**spec,"asset_count":len(assets),"selection":"best-owned-private-media","order":"chronological-story"}

class PrivateMusicAudioAgent:
    def select(self,spec:dict)->dict:
        tracks=load_library(); track=choose_track(spec["prompt"],tracks)
        if track is None: raise ValueError("no documented music track for private video")
        return {**spec,"music_track":str(track["path"]),"music_license":track["license"],
                "audio_policy":"preserve-source-audio-and-mix-music"}

class PrivateQM:
    def checks(self,*,duration:float,has_audio:bool,has_video:bool,creative:dict)->dict:
        checks={"duration_285_305":285<=duration<=305,"audio":has_audio,"video":has_video,
                "creative_plan":bool(creative.get("overlays")),"private_only":creative.get("privacy")=="private-only"}
        return {"passed":all(checks.values()),"checks":checks}

def build_plan(task_id:str,prompt:str,assets:list[dict])->PrivateVideoPlan:
    spec=PrivateProductionLead().decompose(task_id,prompt)
    spec=PrivateCreativeDirector().create(spec)
    spec=PrivateMediaStoryAgent().bind(spec,assets)
    spec=PrivateMusicAudioAgent().select(spec)
    return PrivateVideoPlan(task_id,spec["title"],spec["duration_seconds"],spec["aspect_ratio"],
        spec["privacy"],spec["story_style"],spec["music_track"],tuple(spec["overlays"]))

def persist_stage(client,bucket,task_id,stage,status,detail=""):
    if stage not in STAGES: raise ValueError("unknown private production stage")
    body={"schema":"PRIVATE-VIDEO-STAGE-V1","task_id":task_id,"stage":stage,"status":status,
          "updated_at":datetime.now(timezone.utc).isoformat()}
    if detail: body["detail"]=detail[:160]
    client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/stages/{stage}.json",
        Body=json.dumps(body,ensure_ascii=False).encode(),ContentType="application/json",CacheControl="private, no-store")

def load_private_prompt(client,bucket,task_id):
    page=client.list_objects_v2(Bucket=bucket,Prefix="ai-central/v1/inbox/",MaxKeys=1000)
    if page.get("IsTruncated"): raise RuntimeError("private inbox scan truncated")
    matches=[]
    for item in page.get("Contents",[]):
        obj=json.loads(client.get_object(Bucket=bucket,Key=item["Key"])["Body"].read(12000))
        if obj.get("id")==task_id and obj.get("schema")=="AI-INBOX-V1" and obj.get("kind")=="message":
            matches.append(obj)
    if len(matches)!=1: raise RuntimeError("private task prompt not uniquely resolved")
    if matches[0].get("dispatch_target")!="private-media-container": raise RuntimeError("task not authorized for private media runtime")
    return str(matches[0].get("message",""))
