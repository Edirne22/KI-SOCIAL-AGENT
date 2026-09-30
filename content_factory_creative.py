"""Block 5: Creative Director + Bülent Writing contracts.

Consumes Block-4 verified facts only. Produces creative plans/drafts but has no
fact-promotion, approval, render or publish authority.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib, json, re
from typing import Iterable, Protocol

from content_factory_newsroom import FactPackage, ClaimStatus


class CreativeContractError(ValueError): pass

class ContentFormat(str, Enum):
    POST="post"; IMAGE="image"; CAROUSEL="carousel"; REEL="reel"; VIDEO="video"

@dataclass(frozen=True)
class CreativeRequest:
    platforms: tuple[str,...]=("instagram",)
    preferred_format: str=""
    has_image: bool=False
    has_video: bool=False
    longform_video: bool=False
    objective: str="community"
    language: str="de"

@dataclass(frozen=True)
class StoryBeat:
    beat_id: str
    purpose: str
    fact_claim_ids: tuple[str,...]=()
    visual_intent: str=""

@dataclass(frozen=True)
class CreativeBrief:
    brief_id: str
    fact_package_id: str
    content_format: ContentFormat
    platforms: tuple[str,...]
    hook: str
    angle: str
    beats: tuple[StoryBeat,...]
    allowed_claim_ids: tuple[str,...]
    language: str="de"

@dataclass(frozen=True)
class WritingDraft:
    draft_id: str
    brief_id: str
    caption: str
    hashtags: tuple[str,...]
    used_claim_ids: tuple[str,...]
    discussion_question: str=""
    sentence_claim_map: tuple[tuple[str, tuple[str,...]], ...]=()

@dataclass(frozen=True)
class AudienceSignal:
    persona: str
    kind: str
    note: str

@dataclass(frozen=True)
class AudienceSimulationReport:
    run_id: str
    input_revision: int
    label: str
    signals: tuple[AudienceSignal,...]

class AudiencePersona(Protocol):
    name: str
    def review(self, brief: CreativeBrief, draft: WritingDraft) -> Iterable[AudienceSignal]: ...

class AudiencePanel:
    """Read-only advisory simulation. Never returns claims or authority changes."""
    def __init__(self, personas: Iterable[AudiencePersona]=()):
        self.personas=tuple(personas)
    def review(self, *, job_id: str, revision: int, brief: CreativeBrief, draft: WritingDraft):
        signals=[]
        for persona in self.personas:
            try:
                for signal in persona.review(brief,draft):
                    if not isinstance(signal,AudienceSignal):
                        raise CreativeContractError("persona may return AudienceSignal only")
                    signals.append(signal)
            except Exception as exc:
                signals.append(AudienceSignal(getattr(persona,"name","unknown"),"degraded",type(exc).__name__))
        canonical={"job_id":job_id,"revision":revision,"brief":brief.brief_id,"draft":draft.draft_id,
                   "personas":[getattr(p,"name","unknown") for p in self.personas]}
        run_id=hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()
        return AudienceSimulationReport(run_id,revision,"SIMULATED_AUDIENCE_FEEDBACK",tuple(signals))


class CreativeDirector:
    def choose_format(self, request: CreativeRequest) -> ContentFormat:
        if request.preferred_format:
            try: return ContentFormat(request.preferred_format.lower())
            except ValueError as exc: raise CreativeContractError("unsupported preferred format") from exc
        if request.longform_video: return ContentFormat.REEL
        if request.has_video: return ContentFormat.REEL
        if request.has_image and len(request.platforms)>1: return ContentFormat.IMAGE
        return ContentFormat.POST

    def create_brief(self, package: FactPackage, request: CreativeRequest) -> CreativeBrief:
        if not package.publishable:
            raise CreativeContractError("creative work requires a publishable Block-4 FactPackage")
        verified=package.writer_facts
        if not verified or any(c.status != ClaimStatus.VERIFIED for c in verified):
            raise CreativeContractError("creative input must contain verified writer facts only")
        fmt=self.choose_format(request)
        ids=tuple(c.claim_id for c in verified)
        first=verified[0].statement.strip()
        hook=first if len(first)<=120 else first[:117].rstrip()+"..."
        beats=tuple(StoryBeat(f"beat-{i+1}","fact", (c.claim_id,), "source-led visual") for i,c in enumerate(verified))
        canonical={"package":package.package_id,"format":fmt.value,"platforms":request.platforms,
                   "claims":ids,"language":request.language}
        brief_id=hashlib.sha256(json.dumps(canonical,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        return CreativeBrief(brief_id,package.package_id,fmt,tuple(request.platforms),hook,
                             "fact-first, community-near",beats,ids,request.language)


class BuelentWritingEditor:
    """Deterministic boundary around generated copy.

    An LLM/provider may propose text upstream; this boundary rejects copy that
    introduces factual tokens/numbers outside verified statements or leaks
    internal/source-control language. It never invents facts itself.
    """
    BANNED=("system prompt","ignore previous","verified fact","factpackage","claim_id",
            "source-fact","internal tool","[redacted_instruction]")
    def finalize(self, brief: CreativeBrief, package: FactPackage, *, caption: str,
                 hashtags: Iterable[str]=(), used_claim_ids: Iterable[str]=(),
                 discussion_question: str="", sentence_claim_map: Iterable[tuple[str, Iterable[str]]]=()) -> WritingDraft:
        text=re.sub(r"\s+"," ",str(caption or "")).strip()
        if not text: raise CreativeContractError("caption required")
        low=text.casefold()
        if any(x in low for x in self.BANNED): raise CreativeContractError("internal/injection language leaked into copy")
        allowed=set(brief.allowed_claim_ids); used=tuple(dict.fromkeys(used_claim_ids))
        if not used or not set(used).issubset(allowed): raise CreativeContractError("draft must cite only verified allowed claim ids")
        verified={c.claim_id:c for c in package.writer_facts}
        if package.package_id != brief.fact_package_id: raise CreativeContractError("brief/fact package mismatch")
        # Numbers are high-risk factual precision: every number in public copy
        # must occur in one of the explicitly used verified statements.
        evidence_text=" ".join(verified[c].statement for c in used)
        for number in re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?:%|°)?",text):
            if number not in evidence_text: raise CreativeContractError("draft introduced unverified numeric precision")
        mapping=tuple((re.sub(r"\\s+"," ",str(sentence)).strip(), tuple(dict.fromkeys(ids))) for sentence,ids in sentence_claim_map)
        if not mapping: raise CreativeContractError("sentence-to-claim grounding required")
        mapped_text=" ".join(sentence for sentence,_ in mapping)
        factual_caption=text
        if discussion_question and factual_caption.endswith(discussion_question):
            factual_caption=factual_caption[:-len(discussion_question)].rstrip()
        norm=lambda v: re.sub(r"[^a-z0-9äöüß]+"," ",v.casefold()).strip()
        if norm(mapped_text) != norm(factual_caption):
            raise CreativeContractError("every factual caption sentence must be explicitly grounded")
        for sentence,ids in mapping:
            if not sentence or not ids or not set(ids).issubset(set(used)):
                raise CreativeContractError("invalid sentence claim mapping")
            # Fail closed on novel named/factual vocabulary: each mapped sentence
            # must share meaningful lexical support with its declared claims.
            claim_text=" ".join(verified[i].statement for i in ids)
            words=lambda v:{w for w in re.findall(r"[a-zäöüß]{4,}",v.casefold()) if w not in {"dass","eine","einer","einem","einen","oder","aber","auch","wurde","wird","sind","sein","hatte","haben"}}
            if words(sentence) and not (words(sentence) & words(claim_text)):
                raise CreativeContractError("sentence lacks lexical support from declared verified claim")
        tags=tuple(dict.fromkeys(str(h).strip() for h in hashtags if str(h).strip()))
        if len(tags)>7: raise CreativeContractError("too many hashtags")
        canonical={"brief":brief.brief_id,"caption":text,"hashtags":tags,"claims":used,"question":discussion_question,"mapping":mapping}
        draft_id=hashlib.sha256(json.dumps(canonical,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        return WritingDraft(draft_id,brief.brief_id,text,tags,used,discussion_question,mapping)


def attach_creative_artifacts(job, *, package: FactPackage, brief: CreativeBrief,
                              draft: WritingDraft, audience_report: AudienceSimulationReport|None=None):
    status=getattr(job.status,"value",str(job.status))
    if status in ("ready_for_human","approved","publish_queued","published","rejected"):
        raise CreativeContractError("creative artifacts cannot mutate a human/finalized job")
    if brief.fact_package_id != package.package_id or draft.brief_id != brief.brief_id:
        raise CreativeContractError("creative artifact chain mismatch")
    if audience_report and audience_report.input_revision != job.revision:
        raise CreativeContractError("stale audience simulation revision")
    payload={"fact_package_id":package.package_id,"brief":_brief_dict(brief),"draft":_draft_dict(draft)}
    if audience_report:
        payload["audience"]={"run_id":audience_report.run_id,"input_revision":audience_report.input_revision,
                             "label":audience_report.label,"signals":[s.__dict__ for s in audience_report.signals]}
    slot=f"creative_package:r{job.revision}"
    old=job.metadata.get(slot)
    if old is not None and old != payload: raise CreativeContractError("creative replacement requires a new revision")
    job.metadata[slot]=payload

def _brief_dict(b):
    return {"brief_id":b.brief_id,"fact_package_id":b.fact_package_id,"content_format":b.content_format.value,
            "platforms":list(b.platforms),"hook":b.hook,"angle":b.angle,
            "beats":[{"beat_id":x.beat_id,"purpose":x.purpose,"fact_claim_ids":list(x.fact_claim_ids),"visual_intent":x.visual_intent} for x in b.beats],
            "allowed_claim_ids":list(b.allowed_claim_ids),"language":b.language}
def _draft_dict(d):
    return {"draft_id":d.draft_id,"brief_id":d.brief_id,"caption":d.caption,"hashtags":list(d.hashtags),
            "used_claim_ids":list(d.used_claim_ids),"discussion_question":d.discussion_question,
            "sentence_claim_map":[[s,list(ids)] for s,ids in d.sentence_claim_map]}
