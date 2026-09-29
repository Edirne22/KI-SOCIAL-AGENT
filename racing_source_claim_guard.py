"""Deterministic source-claim strength guard for Racing future/status claims.

The source wording remains the authority.  This module does not ask an LLM to
classify certainty and does not create a second factual database.  It only blocks
a caption from using definitive future/transfer wording when the immutable source
(title/summary) explicitly frames that same story as uncertain/unconfirmed.
"""
import re,unicodedata

VERSION="RACING-SOURCE-CLAIM-GUARD-V1.2"

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
 r"\bwill (?:join|race|move|switch|ride|compete)\b",r"\bhas signed\b",r"\bsign(?:s|ed)?\b",
 r"\bjoins?\b",r"\bsecures?\b",
 r"\bresmen\b",r"\bdogrulandi\b",r"\baciklandi\b",r"\bimzaladi\b",
)
# German editorial wording that upgrades an uncertain source to a settled future fact.
_CAPTION_DEFINITIVE=(
 r"\bsteht (?:fest|klar)\b",r"\bist (?:fix|bestaetigt|bestatigt)\b",r"\bwurde (?:bestaetigt|bestatigt)\b",
 r"\bhat (?:unterschrieben|bestaetigt|bestatigt)\b",r"\b(?:bestaetigt|bestatigt)\b",
 r"\bwechselt\b",r"\bgeht .*\b an den start\b",r"\ban den start geht\b",r"\bfaehrt ab\b",
 r"\bwird (?:wechseln|fahren|starten|antreten)\b",r"\b20\d{2}\s+startet\b[^.!?\n]*\b(?:worldsbk|worldssp|motogp|moto2|moto3)\b",
 r"\bab \d{4} .*\b(?:worldsbk|worldssp|motogp|moto2|moto3)\b",
)
_CAPTION_UNCERTAIN=(
 r"\bsignal\b",r"\bdeutet? .*\bhin\b",r"\b(?:koennte|konnte)\b",r"\bduerfte\b",
 r"\bwird erwartet\b",r"\b(?:moeglich|moglich)\b",r"\bwohl\b",r"\bvermutlich\b",
 r"\bnicht (?:offiziell )?(?:bestaetigt|bestatigt)\b",r"\bnoch nicht (?:bestaetigt|bestatigt)\b",
)

def _any(patterns,text):
    return any(re.search(p,text) for p in patterns)

def _title_has_explicit_confirmation(title):
    cleaned=re.sub(r"\bnot (?:yet )?(?:officially )?confirmed\b"," ",title)
    cleaned=re.sub(r"\bresmen (?:henuz )?dogrulanmadi\b"," ",cleaned)
    return _any(_SOURCE_DEFINITIVE,cleaned)

def _future_transfer_title(title):
    return bool(re.search(r"\b20\d{2}\b",title) and re.search(r"\b(?:worldsbk|worldssp|motogp|moto2|moto3)\b",title))

def source_has_uncertainty(item):
    src=source_text(item)
    title=fold(str(item.get("title","")))
    if _any(_UNCERTAIN,src):
        return True
    # Future-series/transfer headlines are not treated as officially confirmed
    # merely because a generated summary uses definitive wording.
    return _future_transfer_title(title) and not _title_has_explicit_confirmation(title)

def source_has_definitive_confirmation(item):
    title=fold(str(item.get("title","")))
    # The raw/source title is the certainty ceiling. Generated or refreshed
    # summaries are useful context but may never license a stronger future/
    # transfer claim. Definitive wording therefore requires an explicit
    # confirmation marker in the title itself.
    if _any(_UNCERTAIN,title):
        return False
    cleaned=re.sub(r"\bnot (?:yet )?(?:officially )?confirmed\b"," ",title)
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
