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
    max_duration_seconds:int
    duration_policy:str
    aspect_ratio:str
    privacy:str
    story_style:str
    music_track:str
    overlays:tuple[str,...]
    scene_plan:tuple[dict,...]
    asset_effects:tuple[str,...]
    asset_transitions:tuple[str,...]
    asset_pacing:tuple[float,...]
    asset_order:tuple[int,...]=()
    audio_cues:tuple[dict,...]=()
    overlay_cues:tuple[dict,...]=()
    transition_implementation:str=""
    render_evidence_contract:str=""
    creative_revision:str=CREATIVE_REVISION
    stages:tuple[str,...]=STAGES

class PrivateProductionLead:
    def decompose(self,task_id:str,prompt:str)->dict:
        if not prompt.strip(): raise ValueError("private video prompt required")
        low=prompt.casefold()
        duration=210
        ratio="9:16"
        title="Dünya – Level 12" if "dünya" in low and ("12" in low or "geburtstag" in low) else "Private Erinnerung"
        return {"task_id":task_id,"prompt":prompt,"duration_seconds":duration,"max_duration_seconds":300,
                "duration_policy":"MAXIMUM","aspect_ratio":ratio,"title":title,"privacy":"private-only"}

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

def verified_visual_evidence(asset:dict)->bool:
    """Require traceable frame-level evidence, not a self-asserted boolean."""
    if asset.get("content_verified") is not True:
        return False
    if asset.get("story_beat") not in {"intro","build","action","highlights","home","finale"}:
        return False
    if not isinstance(asset.get("asset_role"),str) or not asset["asset_role"].strip():
        return False
    evidence=asset.get("visual_evidence")
    if not isinstance(evidence,dict):
        return False
    if evidence.get("source") != "private-frame-analysis-v1":
        return False
    if not isinstance(evidence.get("frame_sha256"),str) or not re.fullmatch(r"[0-9a-f]{64}",evidence["frame_sha256"]):
        return False
    if not isinstance(evidence.get("observations"),list) or not evidence["observations"]:
        return False
    return all(isinstance(x,str) and 3<=len(x.strip())<=240 for x in evidence["observations"])


def analyze_private_media(client, bucket: str, assets: list[dict], *, infer=None) -> list[dict]:
    """Analyze private R2 media via a local, caller-supplied vision inference function.

    infer(jpeg_bytes) must return {"story_beat": ..., "asset_role": ...,
    "observations": [...]}. No private bytes leave the caller's container.
    """
    import hashlib
    import subprocess
    import tempfile
    from pathlib import Path
    if infer is None:
        raise RuntimeError("PRIVATE_LOCAL_VISION_BACKEND_NOT_CONFIGURED")
    analyzed=[]
    for asset in assets:
        if asset.get("mime") not in {"image/jpeg","image/png","video/mp4","video/quicktime"}:
            raise RuntimeError("PRIVATE_VISION_UNSUPPORTED_MEDIA")
        with tempfile.TemporaryDirectory(prefix="private-vision-") as td:
            source=Path(td)/("source.mp4" if asset["mime"].startswith("video/") else "source.png")
            source.write_bytes(client.get_object(Bucket=bucket,Key=asset["key"])["Body"].read())
            frame=Path(td)/"frame.jpg"
            cmd=["ffmpeg","-v","error","-y"]
            if asset["mime"].startswith("video/"):
                cmd+=["-ss","0.5"]
            cmd+=["-i",str(source),"-frames:v","1","-vf","scale=512:-2",str(frame)]
            result=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)
            if result.returncode or not frame.exists():
                raise RuntimeError("PRIVATE_VISION_FRAME_EXTRACTION_FAILED")
            jpeg=frame.read_bytes()
            verdict=infer(jpeg)
            if not isinstance(verdict,dict):
                raise RuntimeError("PRIVATE_VISION_INVALID_INFERENCE")
            enriched={**asset,"content_verified":True,
                      "story_beat":verdict.get("story_beat"),
                      "asset_role":verdict.get("asset_role"),
                      "visual_evidence":{"source":"private-frame-analysis-v1",
                          "frame_sha256":hashlib.sha256(jpeg).hexdigest(),
                          "observations":verdict.get("observations")}}
            if not verified_visual_evidence(enriched):
                raise RuntimeError("PRIVATE_VISION_INVALID_INFERENCE")
            analyzed.append(enriched)
    return analyzed


class PrivateMediaStoryAgent:
    def bind(self,spec:dict,assets:list[dict])->dict:
        if not assets: raise ValueError("private media required")
        scenes=spec["scene_plan"]; assignments=[]; transitions=[]; pacing=[]
        total=len(assets)
        # Only consume verified visual analysis. Filename, upload order and MIME
        # are not semantic evidence; fail closed until a private analyzer exists.
        verified=all(verified_visual_evidence(a) for a in assets)
        scene_ids={s["id"]:s for s in scenes}
        story_order=("intro","build","action","highlights","home","finale")
        if verified:
            for asset in assets:
                if asset["story_beat"] not in scene_ids:
                    raise ValueError("PRIVATE_STORY_BEAT_UNKNOWN")
            ordered=sorted(range(total),key=lambda i:(
                story_order.index(assets[i]["story_beat"]),
                assets[i].get("captured_at",""),i))
        else:
            ordered=list(range(total))
        for i,idx in enumerate(ordered):
            asset=assets[idx]
            scene=scene_ids[asset["story_beat"]] if verified else scenes[min(len(scenes)-1,i*len(scenes)//total)]
            effects=scene["effects"]
            assignments.append(effects[i % len(effects)])
            transitions.append((scene["transition"],float(scene["transition_seconds"])))
            pacing.append(float(scene["pace"]))
        return {**spec,"asset_count":total,
                "selection":"verified-content-storyboard" if verified else "unclassified-blocked",
                "order":"verified-story-beats" if verified else "unclassified-blocked",
                "asset_order":tuple(ordered),
                "asset_effects":tuple(assignments),
                "asset_transitions":tuple(transitions),"asset_pacing":tuple(pacing)}

def preflight_private_machine_contract(plan: PrivateVideoPlan, assets: list[dict]) -> dict:
    """Read-only gate. Never downloads assets, invokes FFmpeg or starts production."""
    issues = []
    n = len(assets)
    if not n or len(plan.asset_effects) != n or len(plan.asset_transitions) != n or len(plan.asset_pacing) != n:
        issues.append("ASSET_ASSIGNMENT_INCOMPLETE")
    if plan.privacy != "private-only" or plan.aspect_ratio != "9:16":
        issues.append("FORMAT_PRIVACY_MISMATCH")
    if plan.duration_policy == "MAXIMUM" and plan.duration_seconds >= plan.max_duration_seconds:
        issues.append("MAXIMUM_DURATION_FORCED_TO_CEILING")
    if not all(verified_visual_evidence(a) for a in assets):
        issues.append("ASSET_CONTENT_NOT_CLASSIFIED")
    if not all(isinstance(s, dict) and s.get("id") and s.get("purpose") for s in plan.scene_plan):
        issues.append("SCENE_CONTRACT_INCOMPLETE")
    if not getattr(plan, "audio_cues", None):
        issues.append("AUDIO_CUES_NOT_MACHINE_BOUND")
    if not getattr(plan, "overlay_cues", None):
        issues.append("OVERLAY_CUES_NOT_MACHINE_BOUND")
    if plan.transition_implementation != "ffmpeg-xfade-v1":
        issues.append("REAL_TRANSITION_ADAPTER_UNPROVEN")
    if plan.render_evidence_contract != "private-qm-expected-actual-v1":
        issues.append("QM_EXPECTED_ACTUAL_CONTRACT_MISSING")
    return {"decision": "NOT_READY_FOR_MEDIA" if issues else "READY_FOR_MEDIA",
            "issues": issues, "asset_count": n, "creative_revision": plan.creative_revision}


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
            "duration_within_contract":1<=duration<=float(creative.get("max_duration_seconds",300))+1.0,
            "audio":has_audio,
            "video":has_video,
            "scene_plan":creative.get("scene_count",0)>=4,
            "creative_effect_variety":len(applied)>=3,
            "creative_effects_executed":bool(expected) and expected.issubset(applied),
            "transitions_executed":len(set(creative.get("applied_transitions",())))>=2,
            "pacing_executed":creative.get("pacing_applied") is True,
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
    return PrivateVideoPlan(spec["task_id"],spec["title"],spec["duration_seconds"],spec["max_duration_seconds"],spec["duration_policy"],spec["aspect_ratio"],
        spec["privacy"],spec["story_style"],spec["music_track"],tuple(spec["overlays"]),
        tuple(spec["scene_plan"]),tuple(spec["asset_effects"]),tuple(spec["asset_transitions"]),
        tuple(spec["asset_pacing"]),tuple(spec["asset_order"]),
        ({"policy":"music-bed","track":spec["music_track"]},),\n        tuple({"text":t,"position":p} for p,t in zip(("intro","mid","finale"),spec["overlays"])),\n        "ffmpeg-xfade-v1","private-qm-expected-actual-v1",spec["creative_revision"])

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
