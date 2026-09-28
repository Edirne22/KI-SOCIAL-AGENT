"""Deterministic source-claim strength guard for Racing future/status claims.

The source wording remains the authority.  This module does not ask an LLM to
classify certainty and does not create a second factual database.  It only blocks
a caption from using definitive future/transfer wording when the immutable source
(title/summary) explicitly frames that same story as uncertain/unconfirmed.
"""
import re,unicodedata

VERSION="RACING-SOURCE-CLAIM-GUARD-V1"

def fold(value):
    s=unicodedata.normalize("NFKD",str(value or "")).casefold().replace("ı","i")
    return "".join(c for c in s if not unicodedata.combining(c))

def source_text(item):
    return fold(str(item.get("title",""))+" "+str(item.get("summary","")))

# These are source-language markers, not inferred certainty labels.
_UNCERTAIN=(
 r"\bstrong signal\b",r"\bsignal\b",r"\bhint(?:s|ed|ing)?\b",
 r"\blikely\b",r"\bexpected\b",r"\bcould\b",r"\bmay\b",r"\bmight\b",
 r"\breportedly\b",r"\brumou?r(?:ed|s)?\b",r"\bnot (?:yet )?(?:officially )?confirmed\b",
 r"\bguclu sinyal\b",r"\bsinyal\b",r"\bbekleniyor\b",r"\bolabilir\b",
 r"\biddia\b",r"\bsoylenti\b",r"\bresmen (?:henuz )?dogrulanmadi\b",
)
_SOURCE_DEFINITIVE=(
 r"\bconfirmed\b",r"\bofficially confirmed\b",r"\bannounce[ds]?\b",
 r"\bwill (?:join|race|move|switch|ride|compete)\b",r"\bhas signed\b",r"\bsigned\b",
 r"\bjoins?\b",r"\bsecures?\b",
 r"\bresmen\b",r"\bdogrulandi\b",r"\baciklandi\b",r"\bimzaladi\b",
)
# German editorial wording that upgrades an uncertain source to a settled future fact.
_CAPTION_DEFINITIVE=(
 r"\bsteht (?:fest|klar)\b",r"\bist (?:fix|bestaetigt)\b",r"\bwurde bestaetigt\b",
 r"\bhat (?:unterschrieben|bestaetigt)\b",
 r"\bwechselt\b",r"\bgeht .*\b an den start\b",r"\bfaehrt ab\b",
 r"\bwird (?:wechseln|fahren|starten|antreten)\b",
 r"\bab \d{4} .*\b(?:worldsbk|worldssp|motogp|moto2|moto3)\b",
)
_CAPTION_UNCERTAIN=(
 r"\bsignal\b",r"\bdeutet? .*\bhin\b",r"\bkoennte\b",r"\bduerfte\b",
 r"\bwird erwartet\b",r"\bmoeglich\b",r"\bwohl\b",r"\bvermutlich\b",
 r"\bnicht (?:offiziell )?bestaetigt\b",r"\bnoch nicht bestaetigt\b",
)

def _any(patterns,text):
    return any(re.search(p,text) for p in patterns)

def source_has_uncertainty(item):
    src=source_text(item)
    return _any(_UNCERTAIN,src)

def source_has_definitive_confirmation(item):
    src=source_text(item)
    # Explicit negation must not be mistaken for confirmation.
    cleaned=re.sub(r"\bnot (?:yet )?(?:officially )?confirmed\b"," ",src)
    cleaned=re.sub(r"\bresmen (?:henuz )?dogrulanmadi\b"," ",cleaned)
    return _any(_SOURCE_DEFINITIVE,cleaned)

def claim_strength_errors(item,caption,prefix="Source-Claim-Guard"):
    src_uncertain=source_has_uncertainty(item)
    if not src_uncertain or source_has_definitive_confirmation(item):
        return []
    cap=fold(re.sub(r"#[A-Za-z0-9ÄÖÜäöüß]+"," ",str(caption or "")))
    # A caption that preserves uncertainty is safe even if it discusses the
    # possible move.  The guard targets only unqualified definitive assertions.
    if _any(_CAPTION_UNCERTAIN,cap):
        # Split sentences: one disclaimer must not license a separate definitive
        # assertion ("he will join. Contract not confirmed.").
        sentences=[x.strip() for x in re.split(r"[.!?\n]+",cap) if x.strip()]
        definitive=[s for s in sentences if _any(_CAPTION_DEFINITIVE,s) and not _any(_CAPTION_UNCERTAIN,s)]
        if not definitive:return []
    elif not _any(_CAPTION_DEFINITIVE,cap):
        return []
    return [f"{prefix}: definitive Zukunfts-/Transferaussage ist durch unsichere Quellenformulierung nicht gedeckt"]
