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
    # Telegram messages are kept comfortably below the platform limit.
    lines=[f"🏁 Racing {label} – manuelle Auswahl",""]
    for i,x in enumerate(rows,1):
        title=" ".join(str(x.get("title","")).split())
        lines += [f"{i}️⃣ [{x.get('series','Racing')}] {title[:180]}",f"🔗 {x.get('url','')}",""]
    lines += ["Auswählen: racing artikel <Nr>","Beispiel: racing artikel 3"]
    send_message("\n".join(lines)[:3900])
    return len(rows)

def _official_url(url):
    try:
        host=(urlparse(url).hostname or "").lower()
        return any(host==h or host.endswith("."+h) for h in OFFICIAL_HOSTS)
    except Exception:
        return False

def _prepare_one(x):
    x=dict(x)
    x.pop("_pool_day",None)
    agency.lock_source_series(x,x.get("source_series") or x.get("series"))
    x=agency.enrich_turkish(x)
    # Refresh official source facts before the manual article enters QM.
    fresh=agency.article_info(x.get("title",""),x.get("url",""))
    for k in ("title","summary","preview","published_at"):
        if fresh.get(k): x[k]=fresh[k]
    if not agency.qualify_copy(x):
        return False
    b_ok,_=agency.review_batch([x])[0]
    if not b_ok or not agency.finish_item(x,1):
        return False
    now=datetime.now(timezone.utc)
    agency.write_session([x],now)
    agency.telegram_preview([x],agency.is_turkish_focus(x),[x])
    return True

def handle(command):
    c=" ".join(command.strip().split())
    rows,label=_rows_for(c)
    if rows is not None:
        return _show(rows,label)

    m=re.fullmatch(r"racing\s+artikel\s+(\d+)",c,re.I)
    if m:
        n=int(m.group(1))
        try:
            state=json.loads(SELECTION_STATE.read_text(encoding="utf-8"))
            pool=state.get("rows",[])
        except Exception:
            pool=[]
        if not 1<=n<=len(pool):
            send_message("❌ Racing-Artikelnummer nicht vorhanden. Erst 'racing top20', 'racing gestern' oder 'racing suche …' senden.")
            return 0
        ok=_prepare_one(pool[n-1])
        send_message("❌ Artikel ist nicht durch die vollständige QM-Kette gekommen." if not ok else "✅ Artikel durch QM – bitte den neuen MotoGP-Vorschlag in Telegram freigeben.")
        return 1 if ok else 0

    m=re.fullmatch(r"racing\s+url\s+(https?://\S+)",c,re.I)
    if m:
        url=m.group(1)
        if not _official_url(url):
            send_message("❌ racing url akzeptiert nur offizielle MotoGP-/WorldSBK-Quellen.")
            return 0
        x=agency.article_info(url,url)
        x["url"]=url
        agency.lock_source_series(x)
        ok=_prepare_one(x)
        send_message("❌ URL ist nicht durch die vollständige QM-Kette gekommen." if not ok else "✅ URL durch QM – bitte den neuen MotoGP-Vorschlag in Telegram freigeben.")
        return 1 if ok else 0
    return 2

if __name__=="__main__":
    raise SystemExit(0 if handle(" ".join(sys.argv[1:])) != 2 else 2)
