"""Manual Telegram access to the existing Racing QM pool.

Browsing never publishes. A selected article is sent through the same
Racing/Semantic/Chief-QM and Telegram approval session as automatic picks.
"""
from __future__ import annotations
import re, sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from telegram_bot import send_message
import motogp_content_agency_v2 as agency

OFFICIAL_HOSTS = ("motogp.com", "worldsbk.com")\nSELECTION_STATE = Path("memory/RACING_MANUAL_SELECTION.json")

def _norm(s):
    return agency.fold(str(s or ""))

def _all_rows():
    data=agency.load_pool(); out=[]; seen=set()
    for day in sorted(data.get("days",{}), reverse=True):
        for row in data["days"].get(day,[]):
            key=row.get("story_key") or row.get("url")
            if not key or key in seen: continue
            seen.add(key); x=dict(row); x["_pool_day"]=day; out.append(x)
    return out

def _rows_for(command):
    c=" ".join(command.strip().split())
    low=c.casefold()
    rows=_all_rows()
    if low=="racing gestern":
        yesterday=(datetime.now(timezone.utc).date()-timedelta(days=1)).isoformat()
        return [x for x in rows if x.get("_pool_day")==yesterday], "gestern"
    m=re.fullmatch(r"racing\s+suche\s+(.+)",c,re.I)
    if m:
        q=_norm(m.group(1))
        return [x for x in rows if q in _norm(" ".join((x.get("title",""),x.get("summary",""),x.get("turkish_rider",""))))], f"Suche: {m.group(1)}"
    m=re.fullmatch(r"racing\s+top(10|20)",low)
    if m:
        n=int(m.group(1)); return rows[:n], f"Top {n}"
    return None,None

def _show(rows,label):
    if not rows:
        send_message(f"🏁 Racing {label}: keine gespeicherten Treffer.")
        return 0
    SELECTION_STATE.parent.mkdir(parents=True,exist_ok=True)
    SELECTION_STATE.write_text(json.dumps({"label":label,"rows":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Send chunks so Top 20 is fully visible instead of being cut at Telegram's limit.
    for offset in range(0,len(rows),5):
        lines=[f"🏁 Racing {label} – manuelle Auswahl ({offset+1}–{min(offset+5,len(rows))}/{len(rows)})",""]
        for i,x in enumerate(rows[offset:offset+5],offset+1):
            title=" ".join(str(x.get("title","")).split())
            lines += [f"{i}️⃣ [{x.get('series','Racing')}] {title[:180]}",f"🔗 {x.get('url','')}",""]
        if offset+5>=len(rows):
            lines += ["Auswählen: racing artikel <Nr>","Beispiel: racing artikel 3"]
        send_message("\n".join(lines))
    return len(rows)

