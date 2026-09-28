"""Natural-language Telegram query layer for the Racing archive."""
from __future__ import annotations
import json,re
from difflib import SequenceMatcher
from datetime import datetime,timezone,timedelta
from pathlib import Path
from telegram_bot import send_message
import motogp_content_agency_v2 as agency
import racing_manual_selection as manual
from llm_router import quick_chat

STATE=manual.SELECTION_STATE

def norm(s): return agency.fold(str(s or ""))

def canonical_riders(values):
    """Resolve spoken rider names only to unambiguous registry entries."""
    registry=[]
    for name in list(getattr(agency,"RIDERS_V2",()))+list(getattr(agency,"SHARED_TURKISH_ALIASES",())):
        if name and name not in registry:
            registry.append(name)
    resolved=[]
    for value in values or []:
        spoken=norm(value).strip()
        compact=re.sub(r"[^a-z0-9]","",spoken)
        if not compact or compact=="can":
            continue
        # Known speech-to-text substitutions are explicit and still registry-guarded.
        spoken_alias={"alexrenz":"Alex Rins"}.get(compact)
        exact=[name for name in registry if re.sub(r"[^a-z0-9]","",norm(name))==compact]
        if spoken_alias in registry:
            choice=spoken_alias
        elif exact:
            choice=exact[0]
        else:
            scored=[]
            spoken_first=spoken.split()[0] if spoken.split() else ""
            for name in registry:
                candidate=norm(name)
                candidate_compact=re.sub(r"[^a-z0-9]","",candidate)
                # For two-token speech keep first-name affinity; compact speech such as aiogura is handled above.
                if " " in spoken and candidate.split()[0]!=spoken_first:
                    continue
                scored.append((SequenceMatcher(None,compact,candidate_compact).ratio(),name))
            scored.sort(reverse=True)
            if not scored:
                continue
            best_score,best_name=scored[0]
            second_score=scored[1][0] if len(scored)>1 else 0.0
            # Spoken full names with an exact first name may contain a badly transcribed surname
            # (live case: Alex Renz -> Alex Rins). Accept only a unique registry candidate.
            exact_first=(" " in spoken and norm(best_name).split()[0]==spoken_first)
            min_score=0.70 if exact_first else 0.82
            if best_score<min_score or (len(scored)>1 and best_score-second_score<0.08):
                continue
            choice=best_name
        if choice not in resolved:
            resolved.append(choice)
    return resolved

def all_rows():
    data=agency.load_pool(); out=[]; seen=set()
    for day in sorted(data.get("days",{}),reverse=True):
        for row in data["days"].get(day,[]):
            key=row.get("story_key") or row.get("url")
            if not key or key in seen: continue
            seen.add(key); x=dict(row); x["_pool_day"]=day
            # Recompute archive display series with the hardened source-aware classifier.
            detected=agency.series_for_raw(x)
            if detected=="Unsupported" and agency._unsupported_racing_discipline(x):
                x["series"]="Karting"
            elif detected and detected!="Unsupported":
                x["series"]=detected
            out.append(x)
    return out

def published(row):
    key=row.get("story_key") or agency.story_key(row.get("title",""),row.get("url",""))
    return key in agency.published_keys()

def parse_days(low):
    today=datetime.now(timezone.utc).date()
    if "gestern" in low and "vorgestern" in low:
        return {(today-timedelta(days=i)).isoformat() for i in (1,2)},"gestern + vorgestern"
    if "vorgestern" in low:
        return {(today-timedelta(days=2)).isoformat()},"vorgestern"
    if "gestern" in low:
        return {(today-timedelta(days=1)).isoformat()},"gestern"
    m=re.search(r"(?:letzte[nr]?|der letzten)\s+(\d+)\s+tag",low)
    if m:
        n=max(1,min(14,int(m.group(1))))
        return {(today-timedelta(days=i)).isoformat() for i in range(n)},"letzte %d Tage"%n
    if "48 stunden" in low or "zwei tage" in low or "2 tage" in low:
        return {(today-timedelta(days=i)).isoformat() for i in range(2)},"letzte 48 Stunden"
    if "24 stunden" in low or "heute" in low:
        return {today.isoformat()},"heute"
    return None,"Archiv"

def query(text):
    low=norm(text); rows=all_rows(); days,label=parse_days(low)
    if days is not None: rows=[x for x in rows if x.get("_pool_day") in days]
    if any(k in low for k in ("ungepostet","nicht gepostet","noch nicht gepostet")):
        rows=[x for x in rows if not published(x)]; label+=" · ungepostet"
    elif any(k in low for k in ("schon gepostet","bereits gepostet","habe ich gepostet")):
        rows=[x for x in rows if published(x)]; label+=" · bereits gepostet"
    series_map=(("worldssp","WorldSSP"),("wssp","WorldSSP"),("worldsbk","WorldSBK"),("wsbk","WorldSBK"),("moto2","Moto2"),("moto3","Moto3"),("motogp","MotoGP"))
    for token,series in series_map:
        if token in low:
            rows=[x for x in rows if str(x.get("series","")).casefold()==series.casefold()]; label+=" · "+series; break
    turkish=any(k in low for k in ("tuerk","turk","türk"))
    if turkish:
        rows=[x for x in rows if x.get("turkish_rider") or agency.detect_turkish_rider(x)]; label+=" · türkische Rider"
    named=[]
    registry=list(getattr(agency,"RIDERS_V2",()))+list(getattr(agency,"SHARED_TURKISH_ALIASES",()))
    for rider in registry:
        if norm(rider) in low and rider not in named: named.append(rider)
    if named:
        rows=[x for x in rows if any(norm(r) in norm(" ".join((x.get("title",""),x.get("summary",""),x.get("turkish_rider","")))) for r in named)]
        label+=" · "+", ".join(named)
    return rows,label

def is_query(text):
    low=norm(text)
    return bool(any(k in low for k in ("gestern","vorgestern","stunden","tag","bericht","meldung","neuigkeit","was gab","gibt es","gib mir","zeig","liste","ungepostet","gepostet","tuerk","turk","türk","motogp","moto2","moto3","worldsbk","worldssp","wsbk","wssp")) or any(norm(r) in low for r in list(getattr(agency,"RIDERS_V2",()))+list(getattr(agency,"SHARED_TURKISH_ALIASES",()))))

def show(rows,label,initial_limit=None):
    if not rows:
        send_message("🏁 Racing %s: keine gespeicherten Treffer."%label); return 0
    STATE.parent.mkdir(parents=True,exist_ok=True)
    page_limit=10 if initial_limit is None else initial_limit
    visible=rows[:page_limit]
    STATE.write_text(json.dumps({"label":label,"rows":rows,"offset":len(visible)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for off in range(0,len(visible),5):
        lines=["🏁 Racing %s (%d–%d/%d)"%(label,off+1,min(off+5,len(visible)),len(rows)),""]
        for i,x in enumerate(visible[off:off+5],off+1):
            status="✅ bereits gepostet" if published(x) else "🟢 noch nicht gepostet"
            lines += ["%d. [%s] %s"%(i,x.get("series","Racing")," ".join(str(x.get("title","")).split())[:180]),status,"🔗 "+x.get("url",""),""]
        if off+5>=len(visible):
            if len(visible)<len(rows): lines += ["Weitere Treffer: mehr · weiter · die nächsten 10"]
            lines += ["Sag einfach z. B. „Nimm Nummer 4“ oder „Zeig mir mehr“."]
        send_message("\n".join(lines))
    return len(rows)


def interpret(text):
    """Map free German speech to a strict archive-query schema; deterministic parser remains fallback."""
    prompt="""Du bist nur ein Intent-Parser fuer ein Motorrad-Racing-Archiv.
Extrahiere aus der Nutzernachricht ausschliesslich JSON mit:
{"intent":"search|top|more|select|approve|unknown","lane":"archive|motogp|turkish","riders":[],"nationality":"","series":[],"hours":null,"days":null,"from_yesterday":false,"limit":null,"status":"all|posted|unposted","selection":null,"selections":[]}
Verstehe natuerliches, umgangssprachliches Deutsch und Tippfehler. Beispiele: 'die letzten drei von Toprak' => search, rider Toprak, limit 3; 'von gestern bis jetzt die türkischen Fahrer' => nationality Turkish, from_yesterday true; 'alles der letzten 48 Stunden ueber Marc Marquez' => rider Marc Marquez, hours 48.
Bei Freigabe-/Posting-Saetzen extrahiere lane und selections: 'Turkish Rider Nummer eins' => approve,turkish,[1]; 'Turkish Rider fünf' => approve,turkish,[5]; 'MotoGP die drei und vier posten' => approve,motogp,[3,4]. Deutsche Zahlwoerter eins bis fünf verstehen. Niemals Nummern erfinden.
Erfinde keine Fahrer, Zeitraeume oder Filter. 'Can' allein ist niemals ein Fahrername. Antworte NUR mit JSON.
Nachricht: """+str(text)
    try:
        raw=(quick_chat(prompt,task_type="fast_chat") or "").strip()
        raw=re.sub(r"^\x60\x60\x60(?:json)?\s*|\s*\x60\x60\x60$","",raw,flags=re.I|re.S)
        obj=json.loads(raw)
        if not isinstance(obj,dict): return None
        return obj
    except Exception as e:
        print("RACING ARCHIVE NLU fallback:",type(e).__name__,str(e)[:120])
        return None

def query_intent(intent):
    rows=all_rows(); label="Archiv"
    requested_riders=[str(x) for x in intent.get("riders",[]) if str(x).strip()]
    riders=canonical_riders(requested_riders)
    nationality=norm(intent.get("nationality",""))
    series=[str(x) for x in intent.get("series",[]) if str(x).strip()]
    now=datetime.now(timezone.utc)
    hours=int(intent["hours"]) if str(intent.get("hours") or "").isdigit() else None
    days=int(intent["days"]) if str(intent.get("days") or "").isdigit() else None
    if hours:
        cutoff=now-timedelta(hours=max(1,min(hours,24*14)))
        allowed={(now.date()-timedelta(days=i)).isoformat() for i in range((hours//24)+2)}
        rows=[x for x in rows if x.get("_pool_day") in allowed]; label=f"letzte {hours} Stunden"
    elif intent.get("from_yesterday"):
        allowed={now.date().isoformat(),(now.date()-timedelta(days=1)).isoformat()}
        rows=[x for x in rows if x.get("_pool_day") in allowed]; label="gestern bis jetzt"
    elif days:
        allowed={(now.date()-timedelta(days=i)).isoformat() for i in range(max(1,min(days,14)))}
        rows=[x for x in rows if x.get("_pool_day") in allowed]; label=f"letzte {days} Tage"
    if nationality in ("turkish","turkisch","turk","tuerkisch","turkische","türkisch","türkische"):
        rows=[x for x in rows if x.get("turkish_rider") or agency.detect_turkish_rider(x)]; label+=" · türkische Rider"
    if series:
        wanted={norm(x) for x in series}; rows=[x for x in rows if norm(x.get("series","")) in wanted]; label+=" · "+", ".join(series)
    if requested_riders and not riders:
        # Fail closed: an explicit rider request must never degrade into an unfiltered archive dump.
        return [], label+" · "+", ".join(requested_riders)
    if riders:
        wanted=[norm(x) for x in riders]
        rows=[x for x in rows if any(r in norm(" ".join((x.get("title",""),x.get("summary",""),x.get("turkish_rider","")))) for r in wanted)]
        label+=" · "+", ".join(riders)
    status=intent.get("status","all")
    if status=="posted": rows=[x for x in rows if published(x)]
    elif status=="unposted": rows=[x for x in rows if not published(x)]
    limit=intent.get("limit")
    if isinstance(limit,int) and limit>0: rows=rows[:min(limit,100)]
    return rows,label

def show_more():
    try:
        state=json.loads(STATE.read_text(encoding="utf-8"))
        rows=state.get("rows",[]); label=state.get("label","Archiv")
        offset=int(state.get("offset",0))
    except Exception:
        send_message("❌ Keine aktive Racing-Liste. Bitte zuerst z. B. „Zeig mir die Top 20“ senden.")
        return 0
    if not rows:
        send_message("❌ Keine aktive Racing-Liste.")
        return 0
    start=offset; end=min(start+10,len(rows))
    if start>=len(rows):
        send_message("🏁 Ende der gespeicherten Racing-Liste erreicht.")
        return 0
    lines=["🏁 Racing %s (%d–%d/%d)"%(label,start+1,end,len(rows)),""]
    for i,x in enumerate(rows[start:end],start+1):
        status="✅ bereits gepostet" if published(x) else "🟢 noch nicht gepostet"
        lines += ["%d. [%s] %s"%(i,x.get("series","Racing")," ".join(str(x.get("title","")).split())[:180]),status,"🔗 "+x.get("url",""),""]
    state["offset"]=end
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if end<len(rows):
        lines += ["Sag einfach „Zeig mir mehr“ für die nächsten Treffer."]
    else:
        lines += ["Sag einfach z. B. „Nimm Nummer 4“."]
    send_message("\n".join(lines))
    return end-start

def handle(text):
    c=" ".join(str(text or "").strip().split())
    low=norm(c)
    # Existing approval commands always belong to the approval router, never archive NLU.
    if re.fullmatch(r"motogp\s+(?:[1-5]|alle|nein)",low,re.I): return 2
    # Natural-language aliases for the existing deterministic archive browser.
    m=re.fullmatch(r"(?:zeig(?:e)?|gib|liste)(?:\s+mir)?\s+(?:die\s+)?top\s*(10|20)(?:\s+(?:berichte|meldungen|artikel))?",low,re.I)
    if m:
        n=int(m.group(1)); return show(all_rows()[:n],"Top %d"%n,initial_limit=10)
    if re.fullmatch(r"(?:mehr|weiter|nachste(?:n)?(?:\s+10)?|die\s+nachsten\s+10)",low,re.I):
        return show_more()
    m=re.fullmatch(r"(?:t\s*|poste\s+|nimm\s+)(\d+)",c,re.I)
    if m: return manual.handle("racing artikel "+m.group(1))
    # Existing MotoGP approval commands belong to the approval receiver, never NLU.
    if re.fullmatch(r"motogp(?:\s+(?:alle|nein|[1-5](?:[\s,]+[1-5])*|✅|❌))?",low,re.I): return 2
    parsed=interpret(c)
    if parsed:
        intent=parsed.get("intent")
        if intent=="approve":
            lane=str(parsed.get("lane","")).lower()
            nums=[int(n) for n in parsed.get("selections",[]) if str(n).isdigit() and 1<=int(n)<=5]
            if lane in ("motogp","turkish") and nums:
                prefix="turkish " if lane=="turkish" else "motogp "
                return ("approval",prefix+",".join(map(str,nums)))
            return 2
        if intent=="more": return show_more()
        if intent=="select" and isinstance(parsed.get("selection"),int):
            return manual.handle("racing artikel "+str(parsed["selection"]))
        if intent=="top":
            limit=parsed.get("limit")
            if limit in (10,20): return show(all_rows()[:limit],"Top %d"%limit,initial_limit=10)
        if intent=="search":
            rows,label=query_intent(parsed); return show(rows,label)
    if not is_query(c): return 2
    rows,label=query(c); return show(rows,label)

if __name__=="__main__":
    import sys
    result=handle(" ".join(sys.argv[1:]))
    if isinstance(result,tuple) and result and result[0]=="approval":
        print("APPROVAL_COMMAND="+result[1])
        raise SystemExit(3)
    raise SystemExit(0 if result != 2 else 2)
