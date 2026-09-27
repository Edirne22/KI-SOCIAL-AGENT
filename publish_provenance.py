"""Small provenance contract shared by media editors and Meta publishers."""
from __future__ import annotations
import json,re

def media_origin(block):
    image=re.search(r"(?mi)^Bild:\s*(?!auto\s*$)(\S+)",block)
    video=re.search(r"(?mi)^Video:\s*(?!auto\s*$)(\S+)",block)
    source=re.search(r"(?mi)^Quelle:\s*(https?://\S+)",block)
    status=re.search(r"(?mi)^Medienstatus:\s*(.+)$",block)
    if video: kind,path="video",video.group(1)
    elif image: kind,path="image",image.group(1)
    else: kind,path="link" if source else "text",(source.group(1) if source else "")
    return {"version":1,"media_kind":kind,"media_path":path,
            "media_status":status.group(1).strip() if status else "",
            "source_url":source.group(1) if source else ""}

def append_publish_provenance(block,platform,post_id):
    origin=media_origin(block)
    lineage=re.search(r"(?mi)^Quellen-Lineage:\s*(\{.*\})\s*$",block)
    if lineage:
        try:origin["source_lineage"]=json.loads(lineage.group(1))
        except json.JSONDecodeError:origin["source_lineage_raw"]=lineage.group(1)
    origin["platform"]=platform;origin["post_id"]=str(post_id)
    line="Publish-Provenienz: "+json.dumps(origin,ensure_ascii=False,sort_keys=True)
    if re.search(r"(?mi)^Publish-Provenienz:",block):
        return re.sub(r"(?mi)^Publish-Provenienz:.*$",line,block,count=1)
    return block.rstrip()+"\n"+line+"\n"
