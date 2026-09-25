"""Manual Telegram access to the existing Racing QM pool.

Browsing never publishes. A selected article is sent through the same
Racing/Semantic/Chief-QM and Telegram approval session as automatic picks.
"""
from __future__ import annotations
import re, sys, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from telegram_bot import send_message
import motogp_content_agency_v2 as agency
import racing_run_controller as rc

OFFICIAL_HOSTS = ("motogp.com", "worldsbk.com")
SELECTION_STATE = Path("memory/RACING_MANUAL_SELECTION.json")
MANUAL_QM_MAX_ROUNDS = 4

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

def _official_url(url):
    try:
        host=(urlparse(url).hostname or "").lower()
        return any(host==h or host.endswith("."+h) for h in OFFICIAL_HOSTS)
    except Exception:
        return False

def _prepare_one(x):
    selected_ref=x
    x=dict(x)
    x.pop("_pool_day",None)
    agency.lock_source_series(x,x.get("source_series") or x.get("series"))
    x=agency.enrich_turkish(x)
    fresh=agency.article_info(x.get("title",""),x.get("url",""))
    for k in ("title","summary","preview","published_at"):
        if fresh.get(k):
            x[k]=fresh[k]
    # Manual selection is binding on the topic, never on the QM verdict.
    # Keep returning concrete gate feedback to Research/Editor; PASS must still
    # be earned by the unchanged Racing/Semantic/Chief gates.
    copy_ok = False
    feedback = None
    for manual_round in range(1, MANUAL_QM_MAX_ROUNDS + 1):
        copy_ok = agency.qualify_copy(x, feedback)
        if copy_ok:
            break
        feedback = (
            ["Manual-QM Racing: " + e for e in x.get("qm_errors", [])]
            + ["Manual-QM Fakten: " + e for e in x.get("semantic_errors", [])]
        ) or ["Manual-QM: Copy-QM ohne Detailgrund abgelehnt"]
        x["manual_qm_round"] = manual_round
        x["manual_qm_last_errors"] = feedback[:12]
        print(f"MANUAL-QM RETURN round={manual_round}: {x.get('title','')[:90]} | {'; '.join(feedback)[:700]}")
        if manual_round < MANUAL_QM_MAX_ROUNDS:
            agency.reanalyse_source(x, feedback)
    if not copy_ok:
        selected_ref["manual_qm_last_errors"]=x.get("manual_qm_last_errors",[])[:12]
        return False
    b_ok,b_err=agency.review_batch([x])[0]
    if not b_ok:
        x["manual_qm_last_errors"]=["Batch-QM: " + e for e in b_err]
        selected_ref["manual_qm_last_errors"]=x["manual_qm_last_errors"][:12]
        return False
    if not agency.finish_item(x,1):
        x["manual_qm_last_errors"]=["Chief-QM: " + e for e in x.get("chief_errors", [])] or ["Chief-QM/Media: keine Freigabe"]
        selected_ref["manual_qm_last_errors"]=x["manual_qm_last_errors"][:12]
        return False
    now=datetime.now(timezone.utc)
    agency.write_session([x],now)
    # Manual pool selections do not run through racing_v85.begin(), therefore
    # they must create their own approval batch before Telegram exposes the
    # human approval command. Without this hand-off active_batch_id stays empty
    # (or points at an older run) and motogp_telegram_receive_v85 correctly
    # refuses publication.
    bid = rc.batch_id(now)
    data = rc._load()
    stamp = now.isoformat()
    data.setdefault("runs", {})[bid] = {
        "status": "READY_FOR_APPROVAL",
        "started_at": stamp,
        "updated_at": stamp,
        "event": rc.event_name(),
        "github_run_id": rc.github_run_id(),
        "arch_version": rc.ARCH_VERSION,
        "origin": "manual_racing_selection",
        "story_key": x.get("story_key", ""),
    }
    data["active_batch_id"] = bid
    rc._save(data)
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
        selected=pool[n-1]
        ok=_prepare_one(selected)
        if not ok:
            details=selected.get("manual_qm_last_errors",[]) if isinstance(selected,dict) else []
            suffix=("\nLetzter QM-Grund: "+"; ".join(details[:3])) if details else ""
            send_message("❌ Artikel ist nicht durch die vollständige QM-Kette gekommen."+suffix)
        else:
            send_message("✅ Artikel durch QM – bitte den neuen MotoGP-Vorschlag in Telegram freigeben.")
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
