"""Dispatch verified Meta inbox events to platform engagement modules."""
from __future__ import annotations
import json
from pathlib import Path
INBOX=Path("memory/META_ENGAGEMENT_INBOX.jsonl")
def dispatch()->int:
    if not INBOX.exists():return 0
    events=[json.loads(x) for x in INBOX.read_text(encoding="utf-8").splitlines() if x.strip()]
    done=0
    for e in events:
        if e.get("platform")=="instagram":
            import instagram_engagement as target
        elif e.get("platform")=="facebook":
            import facebook_engagement as target
        else:continue
        target.ingest(e);done+=1
    if done:INBOX.write_text("",encoding="utf-8")
    return done
if __name__=="__main__":print(f"META ENGAGEMENT: {dispatch()} Event(s) verarbeitet.")
