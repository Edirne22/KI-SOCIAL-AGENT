"""Conservative, zero-cost YouTube source-quality and coverage triage.

Never infer an official account from display name, follower count or SEO title.
Only explicitly curated exact YouTube channel IDs can be verified. Foreign
scripts/languages are NOT low quality; explicit unrelated channel-topic
metadata plus deceptive racing highlight SEO is a review flag, not a ban.
Title/search/metadata alone NEVER proves video or transcript consumption.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from urllib.parse import urlparse

RACING = re.compile(r"(?i)\b(moto\s*gp|moto[234]|world\s*sbk|world\s*ssp|wsbk|wssp|razgatl[iı]o[gğ]lu|toprak|[öo]nc[üu]|sofuo[gğ]lu)\b")
MISLEADING_FORMAT = re.compile(r"(?i)\b(?:full\s+)?highlights?\b")
OFFTOPIC_CUES = re.compile(r"(?i)\b(?:recipe|cooking|kitchen|cuisine|gardening|makeup|beauty|fashion|cuisine|cocina|receta|kochen|küche|rezepte|طبخ|مطبخ|روتينات|طبخه|طبخة)\b")
YT_CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


@dataclass(frozen=True)
class VideoEvidence:
    channel_verification: str
    triage: str
    coverage: str
    reason: str
    channel_id: str


def _channel_id(item: dict) -> str:
    # Explicit uploader's exact ID only; display URL/name never qualifies.
    for key in ("channelId", "channel_id", "authorChannelId"):
        value=item.get(key)
        if isinstance(value,str) and YT_CHANNEL_ID.fullmatch(value.strip()):
            return value.strip()
    return ""


def _valid_youtube_url(value: object) -> bool:
    if not isinstance(value,str):
        return False
    try:
        u=urlparse(value)
        host=(u.hostname or "").lower()
        if u.scheme!="https":
            return False
        if host in ("youtube.com","www.youtube.com","m.youtube.com"):
            from urllib.parse import parse_qs
            v=parse_qs(u.query).get("v",[""])[0]
            return u.path=="/watch" and bool(VIDEO_ID.fullmatch(v))
        if host in ("youtu.be","www.youtu.be"):
            return bool(VIDEO_ID.fullmatch(u.path.lstrip("/")))
    except ValueError:
        return False
    return False


def review_video(item: dict, *, trusted_channel_ids: frozenset[str]=frozenset()) -> VideoEvidence:
    """Never mark a video as watched merely because its URL was discovered.

    This is metadata-based triage; human-verifiable trusted channel IDs must be
    curated separately. A good channel does not license footage or prove that
    a particular clip's assertions are factual.
    """
    cid=_channel_id(item)
    title=str(item.get("title") or "")
    name=str(item.get("channelTitle") or "")
    # Optional channel 'description' must really be uploader biography, never
    # a video's own search/SEO description.
    bio=str(item.get("channelDescription") or "")
    official=cid!="" and cid in trusted_channel_ids
    verification="CURATED_CHANNEL_ID" if official else "NOT_VERIFIED"
    coverage="METADATA_ONLY"
    if not _valid_youtube_url(item.get("url")):
        return VideoEvidence(verification,"QUARANTINE","METADATA_ONLY","invalid_original_youtube_video_url",cid)
    if not title.strip():
        return VideoEvidence(verification,"QUARANTINE","METADATA_ONLY","missing_video_title",cid)
    # A mislabelled uploader biography is never enough for rejecting a source
    # without the clearly SEO-driven 'highlights' claim; uncertain cases stay
    # research-only instead of being silently dropped.
    unrelated=bool(OFFTOPIC_CUES.search(name+" "+bio)) and not bool(RACING.search(name+" "+bio))
    if not official and unrelated and RACING.search(title) and MISLEADING_FORMAT.search(title):
        return VideoEvidence(verification,"QUARANTINE","METADATA_ONLY",
                             "racing_highlights_on_explicitly_unrelated_channel_review_required",cid)
    if official:
        return VideoEvidence(verification,"CHANNEL_CONFIRMED_METADATA_ONLY","METADATA_ONLY",
                             "exact_manually_curated_channel_id_not_content_verification",cid)
    return VideoEvidence(verification,"RESEARCH_ONLY","METADATA_ONLY",
                         "channel_identity_or_video_content_not_independently_verified",cid)


def filter_results(rows: list[dict], *, trusted_channel_ids: frozenset[str]=frozenset()):
    """Preserve both sets with provenance; only explicit anomalies quarantine."""
    accepted=[]
    quarantined=[]
    for item in rows:
        report=review_video(item,trusted_channel_ids=trusted_channel_ids)
        (quarantined if report.triage=="QUARANTINE" else accepted).append((item,report))
    return accepted,quarantined
