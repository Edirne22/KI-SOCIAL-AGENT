"""Discovery and Editorial Scheduler layer for the Edirne 22 Content Factory.

Provides provider-agnostic domain contracts, normalization, exact deduplication,
story-clustering, Turkish-rider priority scoring, event triggers, and race weekend scheduling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from enum import Enum
import hashlib
import json
import re
import unicodedata
from typing import Any, Dict, List, Optional, Protocol, Tuple, Set

from autonomous_editorial import AutonomousEditorialDesk, EditorialDecision, EditorialTrigger, TriggerKind
from turkish_rider_names import canonical_rider, CANONICAL_ALIASES


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fold_text(value: str) -> str:
    """Fold diacritics and case for deterministic matching."""
    s = unicodedata.normalize("NFKD", str(value or "").casefold()).replace("ı", "i")
    return "".join(ch for ch in s if not unicodedata.combining(ch)).replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ş", "s").replace("ç", "c")


def normalize_url(url: str) -> str:
    """Clean and normalize URL for exact deduplication."""
    u = str(url or "").strip()
    if not u:
        return ""
    # Strip common tracking parameters
    u = re.sub(r"[\?&](utm_[^&]+|fbclid|gclid|ref|source)=[^&]*", "", u)
    if u.endswith("?") or u.endswith("&"):
        u = u[:-1]
    # Strip trailing slashes
    if u.startswith("http://") or u.startswith("https://"):
        parts = u.split("#", 1)[0].rstrip("/")
        return parts
    return u


def sanitize_untrusted_text(text: str) -> str:
    """Treat external content as untrusted source content, neutralizing instruction injection."""
    if not text:
        return ""
    # Remove system/prompt injection marker attempts
    cleaned = re.sub(r"(?i)(system\s*prompt|ignore\s*previous\s*instructions|you\s*are\s*now|override\s*guardrails)", "[REDACTED_INSTRUCTION]", text)
    return cleaned.strip()


class SourceType(str, Enum):
    APIFY = "apify"
    RSS = "rss"
    RACING = "racing"
    TURKISH_RIDER = "turkish_rider"
    YOUTUBE = "youtube"
    TELEGRAM = "telegram"
    MANUAL = "manual"


ALLOWED_RACING_SERIES = {"MotoGP", "Moto2", "Moto3", "WorldSBK", "WorldSSP", "WorldSSP300", "WorldSPB", "Moto4", "Karting"}


@dataclass(frozen=True)
class DiscoverySource:
    source_id: str
    name: str
    source_type: SourceType
    trust_score: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.name.strip():
            raise ValueError("source_id and name are required")
        if not 0.0 <= self.trust_score <= 1.0:
            raise ValueError("trust_score must be between 0.0 and 1.0")


@dataclass
class DiscoveryItem:
    item_id: str
    source_id: str
    url: str
    title: str
    text: str = ""
    published_at: str = field(default_factory=utc_now)
    discovered_at: str = field(default_factory=utc_now)
    language: str = "de"
    series: str = ""
    entities: List[str] = field(default_factory=list)
    source_type: str = "racing"
    provenance: str = ""
    confidence: float = 1.0
    relevance: int = 0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        self.url = normalize_url(self.url)
        self.title = sanitize_untrusted_text(self.title)
        self.text = sanitize_untrusted_text(self.text)
        if not self.provenance:
            self.provenance = f"{self.source_type}:{self.source_id}"
        # Entity extraction for Turkish riders if not explicitly provided
        full_txt = f"{self.title} {self.text}"
        extracted = canonical_rider(full_txt)
        if not extracted:
            # Fallback for surname / key name matching (e.g. Razgatlıoğlu, Öncü, Sofuoğlu, Toprak)
            low = fold_text(full_txt)
            if re.search(r"(?<![a-z])(razgatlioglu|toprak)(?![a-z])", low):
                extracted = "Toprak Razgatlıoğlu"
            elif re.search(r"(?<![a-z])bahattin(?![a-z])", low):
                extracted = "Bahattin Sofuoğlu"
            elif re.search(r"(?<![a-z])zayn(?![a-z])", low):
                extracted = "Zayn Sofuoğlu"
            elif re.search(r"(?<![a-z])can(?![a-z])\s*oncu", low):
                extracted = "Can Öncü"
            elif re.search(r"(?<![a-z])deniz(?![a-z])\s*oncu", low):
                extracted = "Deniz Öncü"
            elif re.search(r"(?<![a-z])sofuoglu(?![a-z])", low):
                extracted = "Kenan Sofuoğlu"
        if extracted and extracted not in self.entities:
            self.entities.append(extracted)
        # Infer series from rider context if series is not set
        if not self.series and extracted:
            from turkish_rider_names import context_for
            ctx = context_for(extracted)
            if ctx and ctx.get("series"):
                self.series = ctx["series"]

    @property
    def canonical_hash(self) -> str:
        """Deterministic fingerprint of normalized item identity."""
        data = f"{self.url}|{fold_text(self.title)}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass
class DiscoveryCluster:
    cluster_id: str
    primary_item: DiscoveryItem
    items: List[DiscoveryItem] = field(default_factory=list)
    series: str = ""
    entities: List[str] = field(default_factory=list)
    top_rider: Optional[str] = None
    relevance: int = 0
    is_breaking: bool = False
    is_turkish_rider: bool = False
    summary: str = ""

    def __post_init__(self) -> None:
        if not self.items:
            self.items = [self.primary_item]
        if not self.series:
            self.series = self.primary_item.series
        # Collect all entities
        ent_set: Set[str] = set(self.entities)
        for it in self.items:
            ent_set.update(it.entities)
        self.entities = sorted(list(ent_set))
        # Identify top rider
        for ent in self.entities:
            if ent in CANONICAL_ALIASES:
                self.top_rider = ent
                self.is_turkish_rider = True
                break


class DiscoveryAdapter(Protocol):
    name: str
    source_type: SourceType

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        ...


class DiscoveryCoordinator:
    """Orchestrates ingestion across adapters, deduplication, clustering, scoring, and trigger routing."""

    def __init__(
        self,
        adapters: List[DiscoveryAdapter] = None,
        editorial_desk: Optional[AutonomousEditorialDesk] = None,
    ) -> None:
        self.adapters: List[DiscoveryAdapter] = adapters or []
        self.editorial_desk = editorial_desk
        self._seen_urls: Set[str] = set()
        self._seen_hashes: Set[str] = set()

    def add_adapter(self, adapter: DiscoveryAdapter) -> None:
        self.adapters.append(adapter)

    def deduplicate(self, items: List[DiscoveryItem]) -> List[DiscoveryItem]:
        """Exact URL and canonical title/url hash deduplication."""
        unique: List[DiscoveryItem] = []
        for item in items:
            u = item.url
            h = item.canonical_hash
            if u and u in self._seen_urls:
                continue
            if h in self._seen_hashes:
                continue
            if u:
                self._seen_urls.add(u)
            self._seen_hashes.add(h)
            unique.append(item)
        return unique

    def cluster_items(self, items: List[DiscoveryItem], time_window_hours: int = 48) -> List[DiscoveryCluster]:
        """Groups items belonging to the same story by series, rider/entities, and time proximity."""
        clusters: List[DiscoveryCluster] = []
        for item in items:
            assigned = False
            for cluster in clusters:
                if self._is_same_story(item, cluster, time_window_hours):
                    cluster.items.append(item)
                    if item.relevance > cluster.primary_item.relevance:
                        cluster.primary_item = item
                    # Merge entities
                    ent_set = set(cluster.entities) | set(item.entities)
                    cluster.entities = sorted(list(ent_set))
                    if not cluster.top_rider:
                        for ent in cluster.entities:
                            if ent in CANONICAL_ALIASES:
                                cluster.top_rider = ent
                                cluster.is_turkish_rider = True
                                break
                    assigned = True
                    break
            if not assigned:
                c_id = hashlib.sha256(f"cluster:{item.canonical_hash}".encode("utf-8")).hexdigest()[:16]
                clusters.append(
                    DiscoveryCluster(
                        cluster_id=c_id,
                        primary_item=item,
                        items=[item],
                        series=item.series,
                        entities=list(item.entities),
                        relevance=item.relevance,
                    )
                )
        # Recalculate cluster relevance and properties
        for cluster in clusters:
            self._score_cluster(cluster)
        return clusters

    def _is_same_story(self, item: DiscoveryItem, cluster: DiscoveryCluster, time_window_hours: int) -> bool:
        # Enforce the declared time window before semantic clustering.
        try:
            left = datetime.fromisoformat(item.published_at.replace("Z", "+00:00"))
            right = datetime.fromisoformat(cluster.primary_item.published_at.replace("Z", "+00:00"))
            if left.tzinfo is None:
                left = left.replace(tzinfo=timezone.utc)
            if right.tzinfo is None:
                right = right.replace(tzinfo=timezone.utc)
            if abs((left - right).total_seconds()) > time_window_hours * 3600:
                return False
        except (TypeError, ValueError):
            return False
        # Same rider/entity or exact series + high title word overlap
        item_rider = next((e for e in item.entities if e in CANONICAL_ALIASES), None)
        cluster_rider = cluster.top_rider
        if item_rider and cluster_rider and item_rider == cluster_rider:
            # Check non-rider title word overlap
            rider_words = set(fold_text(item_rider).split())
            t1_words = set(fold_text(item.title).split()) - rider_words
            t2_words = set(fold_text(cluster.primary_item.title).split()) - rider_words
            overlap = t1_words & t2_words
            if len(overlap) >= 2 or fold_text(item.title) in fold_text(cluster.primary_item.title):
                return True
        # Exact URL or source match handled by dedupe. Check title similarity
        t1 = fold_text(item.title)
        t2 = fold_text(cluster.primary_item.title)
        if t1 == t2:
            return True
        words1 = set(t1.split())
        words2 = set(t2.split())
        if words1 and words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
            if jaccard > 0.35 and (item.series == cluster.series or not item.series or not cluster.series):
                return True
        return False

    def _score_cluster(self, cluster: DiscoveryCluster) -> None:
        """Calculates reproducible relevance priority score (0..100)."""
        score = 50  # baseline
        primary = cluster.primary_item

        # 1. Turkish Rider Priority Boost
        if cluster.is_turkish_rider or cluster.top_rider:
            score += 35

        # 2. Breaking / Urgent keywords
        title_low = fold_text(primary.title)
        if any(w in title_low for w in ("eilmeldung", "breaking", "official", "bestatigt", "sofort", "sturz", "sieg", "pdm", "pole")):
            score += 15
            cluster.is_breaking = True

        # 3. Known Racing Series
        if primary.series in ALLOWED_RACING_SERIES:
            score += 10

        # 4. Multi-source validation boost
        if len(cluster.items) > 1:
            score += min(15, len(cluster.items) * 5)

        # Cap score between 0 and 100
        cluster.relevance = max(0, min(100, score))

    def create_editorial_trigger(self, cluster: DiscoveryCluster) -> EditorialTrigger:
        """Converts a story cluster into a deterministic EditorialTrigger."""
        sources = list(set(it.url for it in cluster.items if it.url))
        rider = cluster.top_rider or (cluster.entities[0] if cluster.entities else None)
        # Deterministic trigger_id based on rider/series/primary hash
        trigger_key = f"{rider or 'general'}:{cluster.series or 'racing'}:{cluster.primary_item.canonical_hash}"
        trigger_id = hashlib.sha256(trigger_key.encode("utf-8")).hexdigest()[:16]

        return EditorialTrigger(
            trigger_id=f"trig-{trigger_id}",
            kind=TriggerKind.EVENT,
            title=cluster.primary_item.title,
            series=cluster.series or "Racing",
            source_urls=sources,
            rider=rider,
            relevance=cluster.relevance,
            requested_formats=["reel", "post"],
        )

    def process_all(self, limit_per_adapter: int = 50) -> Tuple[List[DiscoveryItem], List[DiscoveryCluster], List[EditorialDecision]]:
        """Executes full discovery sweep across all adapters, dedupes, clusters, and routes to EditorialDesk."""
        raw_items: List[DiscoveryItem] = []
        for adapter in self.adapters:
            try:
                items = adapter.fetch_items(limit=limit_per_adapter)
                raw_items.extend(items)
            except Exception as exc:
                print(f"[DISCOVERY] Adapter error ({adapter.name}): {exc}")

        deduped = self.deduplicate(raw_items)
        clusters = self.cluster_items(deduped)
        decisions: List[EditorialDecision] = []

        if self.editorial_desk:
            for cluster in clusters:
                trigger = self.create_editorial_trigger(cluster)
                decision = self.editorial_desk.consider(trigger)
                decisions.append(decision)

        return deduped, clusters, decisions


class RaceWeekendScheduler:
    """Timezone-aware scheduler for race weekend candidate creation (Tue/Wed preview -> Fri practice -> Sat quali -> Sun race)."""

    def __init__(self, editorial_desk: AutonomousEditorialDesk, calendar_path: str = "memory/RACE_CALENDAR.json") -> None:
        self.editorial_desk = editorial_desk
        self.calendar_path = calendar_path

    def check_upcoming_events(self, now_dt: Optional[datetime] = None) -> List[EditorialDecision]:
        """Checks local calendar using explicit Berlin / UTC timezone and triggers weekend pre-production if matching schedule windows."""
        if now_dt is None:
            # Default to current Europe/Berlin or UTC
            now_dt = datetime.now(timezone.utc)

        # Explicit timezone handling
        berlin_tz = ZoneInfo("Europe/Berlin")
        local_date = now_dt.astimezone(berlin_tz).date()
        weekday = local_date.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun

        events = self._load_calendar()
        decisions: List[EditorialDecision] = []

        for event in events:
            try:
                start_str = event.get("date_start", "")
                if not start_str:
                    continue
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_str = event.get("date_end", start_str)
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

                days_to_start = (start_date - local_date).days
                series = event.get("series", "MotoGP")
                track = event.get("track", "Unknown Track")

                # Schedule trigger logic based on day of week & days to race
                should_trigger = False
                phase = ""

                if 0 <= days_to_start <= 4:
                    if weekday in (1, 2) and days_to_start in (2, 3, 4):  # Tue / Wed Preview
                        should_trigger = True
                        phase = "Preview & Schedule"
                    elif weekday == 4 and days_to_start in (0, 1, 2):  # Friday Practice
                        should_trigger = True
                        phase = "Practice Session Update"
                    elif weekday == 5 and (start_date <= local_date <= end_date or days_to_start in (0, 1)):  # Sat Quali / Sprint
                        should_trigger = True
                        phase = "Qualifying & Sprint"
                    elif weekday == 6 and (start_date <= local_date <= end_date or days_to_start == 0):  # Sun Race
                        should_trigger = True
                        phase = "Race & Final Results"

                if should_trigger:
                    trigger_key = f"schedule:{series}:{track}:{start_str}:{local_date.isoformat()}:{phase}"
                    trigger_id = f"sched-{hashlib.sha256(trigger_key.encode('utf-8')).hexdigest()[:16]}"
                    trigger = EditorialTrigger(
                        trigger_id=trigger_id,
                        kind=TriggerKind.SCHEDULE,
                        title=f"{series} {track} - {phase}",
                        series=series,
                        event_name=f"{series} {track}",
                        relevance=95,
                        requested_formats=["schedule-carousel", "weekend-preview-reel"],
                    )
                    decision = self.editorial_desk.consider(trigger)
                    decisions.append(decision)
            except Exception as exc:
                print(f"[SCHEDULER] Error processing calendar event {event}: {exc}")

        return decisions

    def _load_calendar(self) -> List[Dict[str, Any]]:
        try:
            with open(self.calendar_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("events", [])
        except Exception as exc:
            print(f"[SCHEDULER] Could not load calendar from {self.calendar_path}: {exc}")
            return []
