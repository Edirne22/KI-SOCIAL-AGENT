"""Deterministic provenance guard for explicit Racing place/team claims.

Narrow fallback protection for Semantic-QM outages. It does not try to NER all prose:
only explicit high-risk constructions are checked against immutable title+summary.
"""
import re,unicodedata
VERSION="RACING-SOURCE-ENTITY-GUARD-V1"
def fold(s):
    s=unicodedata.normalize("NFKD",str(s or "")).replace("ı","i")
    return "".join(c for c in s if not unicodedata.combining(c)).casefold()
def source_text(item):
    return fold((item.get("title") or "")+" "+(item.get("summary") or "")+" "+(item.get("url") or ""))
_STOP={"dem","der","den","das","die","einem","einer","einen","op","tisch","start","ziel","platz","spitze","rennen","race","runde","round","aktion"}
def _place_supported(ent,src):
    ef=fold(ent)
    if ef in src:return True
    from racing_geo_lexicon import RACE_GEO
    for de,row in RACE_GEO.items():
      aliases=[de]+list(row.get("tr",[]))+list(row.get("en",[]))+list(row.get("circuits",[]))
      folded=[fold(a) for a in aliases]
      if ef in folded:return any(a in src for a in folded)
    return False
def _entity(raw):
    raw=re.sub(r"[^A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü0-9-]+$","",raw.strip())
    return raw
def errors(item,caption,prefix="Source-Entity-Guard"):
    src=source_text(item); text=re.sub(r"#[^\s]+","",caption or "")
    out=[]
    # Explicit location claims: in/bei/aus + capitalized proper noun.
    for m in re.finditer(r"\b(?:in|bei|aus)\s+([A-ZÄÖÜÇĞİŞ][A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü-]{2,})\b",text):
        ent=_entity(m.group(1))
        if fold(ent) in _STOP: continue
        if not _place_supported(ent,src): out.append(f"{prefix}: Ort nicht in Quelle: {ent}")
    # Explicit team/manufacturer relationship. Require an obvious team/manufacturer noun
    # or a capitalized entity after für/bei; ordinary phrases remain untouched.
    patterns=[
      r"\b(?:fuer|für|bei)\s+(?:das\s+|dem\s+)?([A-ZÄÖÜÇĞİŞ][A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü0-9-]*(?:-[A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü0-9-]+)*(?:\s+(?:Werksteam|Team|Racing))?)\b",
      r"\b([A-ZÄÖÜÇĞİŞ][A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü0-9-]*(?:-[A-Za-zÄÖÜäöüßÇçĞğİıÖöŞşÜü0-9-]+)*-(?:Werksteam|Team))\b",
    ]
    for pat in patterns:
      for m in re.finditer(pat,text):
        ent=_entity(m.group(1))
        ef=fold(ent)
        if ef in _STOP or ef in src: continue
        # "bei Japan" etc is a place and already covered; here relationship nouns/capitalized
        # entities are fail-closed because the editor is forbidden to invent teams/manufacturers.
        if any(k in ef for k in ("team","racing","werk")) or (re.search(r"\b(?:fuer|für)\s+",m.group(0)) and re.search(r"\b(?:faehrt|fahrt|fährt|startet|wechselt|vertrag|unterschreibt|pilotiert)\b",text,re.I)):
            msg=f"{prefix}: Team/Hersteller nicht in Quelle: {ent}"
            if msg not in out: out.append(msg)
    return out
