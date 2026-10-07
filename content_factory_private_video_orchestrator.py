"""Private video production orchestrator. Private media never reaches a social publisher."""
from __future__ import annotations
from dataclasses import dataclass
import json, re
from datetime import datetime, timezone
from music_agent import load_library, choose_track

STAGES=("production_lead","creative_director","media_story","music_audio","video_editor_ffmpeg","qm","private_preview")
CREATIVE_REVISION="duenya-creative-v2"
MOTION_MODES=("zoom_in","pan_left","zoom_out","pan_right")

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
    scene_plan:tuple[dict,...]
    asset_effects:tuple[str,...]
    asset_transitions:tuple[str,...]
    asset_pacing:tuple[float,...]
    creative_revision:str=CREATIVE_REVISION
    stages:tuple[str,...]=STAGES

class PrivateProductionLead:
    def decompose(self,task_id:str,prompt:str)->dict:
        if not prompt.strip(): raise ValueError("private video prompt required")
        low=prompt.casefold()
        duration=300
        ratio="9:16"
        title="Dünya – Level 12" if "dünya" in low and ("12" in low or "geburtstag" in low) else "Private Erinnerung"
        return {"task_id":task_id,"prompt":prompt,"duration_seconds":duration,"aspect_ratio":ratio,
                "title":title,"privacy":"private-only"}

class PrivateCreativeDirector:
    """Turns the owner's private brief into an executable, privacy-safe scene contract."""
    def create(self,spec:dict)->dict:
        p=spec["prompt"]; low=p.casefold()
        if "dünya" in low:
            overlays=("Dünya – Level 12","12 Jahre voller Erinnerungen","Alles Gute zum 12. Geburtstag, Dünya!")
        else:
            overlays=tuple(x.strip() for x in re.findall(r'["“]([^"”]{2,80})["”]',p)[:3])
        scenes=(
            {"id":"intro","start":0.00,"end":0.10,"purpose":"opening-memory","effects":("zoom_in","pan_right"),"transition":"soft_fade","transition_seconds":0.65,"pace":1.12},
            {"id":"build","start":0.10,"end":0.30,"purpose":"arrival-build-up","effects":("pan_left","zoom_in"),"transition":"soft_fade","transition_seconds":0.50,"pace":1.00},
            {"id":"action","start":0.30,"end":0.62,"purpose":"birthday-action","effects":("zoom_in","pan_right","pan_left"),"transition":"quick_fade","transition_seconds":0.22,"pace":0.78},
            {"id":"highlights","start":0.62,"end":0.78,"purpose":"people-highlights","effects":("zoom_out","pan_left"),"transition":"soft_fade","transition_seconds":0.45,"pace":0.92},
            {"id":"home","start":0.78,"end":0.92,"purpose":"cake-emotion","effects":("zoom_out","pan_right"),"transition":"long_fade","transition_seconds":0.80,"pace":1.15},
            {"id":"finale","start":0.92,"end":1.01,"purpose":"birthday-finale","effects":("zoom_in","zoom_out"),"transition":"long_fade","transition_seconds":0.90,"pace":1.20},
        )
        return {**spec,"story_style":"emotional-modern-memory-story","overlays":overlays,
                "scene_plan":scenes,"creative_revision":CREATIVE_REVISION}

class PrivateMediaStoryAgent:
    def bind(self,spec:dict,assets:list[dict])->dict:
        if not assets: raise ValueError("private media required")
        scenes=spec["scene_plan"]; assignments=[]; transitions=[]; pacing=[]
        total=len(assets)
        for i,_asset in enumerate(assets):
            pos=(i+0.5)/total
            scene=next((s for s in scenes if s["start"]<=pos<s["end"]),scenes[-1])
            effects=scene["effects"]
            assignments.append(effects[i % len(effects)])
            transitions.append((scene["transition"],float(scene["transition_seconds"])))
            pacing.append(float(scene["pace"]))
        return {**spec,"asset_count":total,"selection":"best-owned-private-media",
                "order":"chronological-story","asset_effects":tuple(assignments),
                "asset_transitions":tuple(transitions),"asset_pacing":tuple(pacing)}

class PrivateMusicAudioAgent:
    def select(self,spec:dict)->dict:
        tracks=load_library(); track=choose_track(spec["prompt"],tracks)
        if track is None: raise ValueError("no documented music track for private video")
        return {**spec,"music_track":str(track["path"]),"music_license":track["license"],
                "audio_policy":"preserve-source-audio-and-mix-music"}

class PrivateQM:
    def checks(self,*,duration:float,has_audio:bool,has_video:bool,creative:dict)->dict:
        expected=set(creative.get("expected_effects",()))
        applied=set(creative.get("applied_effects",()))
        checks={
            "duration_285_305":285<=duration<=305,
            "audio":has_audio,
            "video":has_video,
            "scene_plan":creative.get("scene_count",0)>=4,
            "creative_effect_variety":len(applied)>=3,
            "creative_effects_executed":bool(expected) and expected.issubset(applied),
            "overlays_rendered":creative.get("overlays_rendered",0)>=3,
            "creative_revision":creative.get("creative_revision")==CREATIVE_REVISION,
            "private_only":creative.get("privacy")=="private-only",
        }
        return {"passed":all(checks.values()),"checks":checks}

def build_plan(task_id:str,prompt:str,assets:list[dict])->PrivateVideoPlan:
    spec=PrivateProductionLead().decompose(task_id,prompt)
    spec=PrivateCreativeDirector().create(spec)
    spec=PrivateMediaStoryAgent().bind(spec,assets)
    spec=PrivateMusicAudioAgent().select(spec)
    return PrivateVideoPlan(spec["task_id"],spec["title"],spec["duration_seconds"],spec["aspect_ratio"],
        spec["privacy"],spec["story_style"],spec["music_track"],tuple(spec["overlays"]),
        tuple(spec["scene_plan"]),tuple(spec["asset_effects"]),tuple(spec["asset_transitions"]),
        tuple(spec["asset_pacing"]),spec["creative_revision"])

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
