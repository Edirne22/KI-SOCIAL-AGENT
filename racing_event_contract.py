"""Deterministic event/session facts shared by every Racing QM gate.

Only immutable source text (title, summary, URL slug) may create these facts.
Editor/caption text is inspected only for contradictions; it never sets source facts.
"""
import re, unicodedata

SESSION_VERSION="RACING-EVENT-SESSION-V1"

def fold(value):
    s=unicodedata.normalize("NFKD",str(value or "")).casefold().replace("ı","i")
    return "".join(c for c in s if not unicodedata.combining(c))

def _normalized(value):
    s=fold(value).replace("_"," ").replace("-"," ")
    return re.sub(r"\s+"," ",s).strip()

def detect_session(text):
    t=_normalized(text)
    # Most specific first. Turkish "yarisi/yaris" means race, not qualifying.
    patterns=(
        ("Superpole Race",(r"\bsuperpole\s+(?:race|yarisi|yaris)\b",)),
        ("Race 1",(r"\b(?:race|yaris|yarisi)\s*1\b",r"\b1\.?\s*(?:race|yaris|yarisi)\b")),
        ("Race 2",(r"\b(?:race|yaris|yarisi)\s*2\b",r"\b2\.?\s*(?:race|yaris|yarisi)\b")),
        ("FP1",(r"\bfp\s*1\b",r"\bfree practice\s*1\b",r"\bserbest antrenman\s*1\b")),
        ("FP2",(r"\bfp\s*2\b",r"\bfree practice\s*2\b",r"\bserbest antrenman\s*2\b")),
        ("FP3",(r"\bfp\s*3\b",r"\bfree practice\s*3\b",r"\bserbest antrenman\s*3\b")),
        ("Sprint",(r"\bsprint(?:\s+race|\s+yarisi|\s+yaris)?\b",)),
        ("Qualifying",(r"\bqualifying\b",r"\bqualification\b",r"\bsiralama(?:\s+turlari)?\b")),
        # Bare Superpole is the qualifying session only when the source/caption
        # did not match the more specific Superpole Race above.
        ("Superpole",(r"\bsuperpole\b",)),
    )
    for session,regexes in patterns:
        if any(re.search(p,t) for p in regexes):
            return session
    return ""

def source_event_contract(item):
    title=str(item.get("title",""))
    summary=str(item.get("summary",""))
    url=str(item.get("url",""))
    # Title is strongest, then URL slug, then summary. This prevents a summary
    # mentioning another session from overriding the article's explicit subject.
    for field,value in (("title",title),("url",url),("summary",summary)):
        session=detect_session(value)
        if session:
            return {"version":SESSION_VERSION,"session":session,"source_field":field}
    return {"version":SESSION_VERSION,"session":"","source_field":""}

def caption_session(caption):
    editorial=re.sub(r"#[A-Za-z0-9ÄÖÜäöüß]+"," ",str(caption or ""))
    return detect_session(editorial)

def session_errors(item,caption,prefix="Event-Session-Contract"):
    source=source_event_contract(item)
    claimed=caption_session(caption)
    expected=source["session"]
    if expected and claimed and claimed!=expected:
        return [f"{prefix}: Session widerspricht Quelle (Quelle {expected}, Text {claimed})"]
    return []
