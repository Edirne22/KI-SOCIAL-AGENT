"""Compatibility facade: existing Turkish scout plus dedicated MotoEtkinlik discovery."""
from turkish_riders_scout import *  # noqa: F401,F403
import turkish_riders_scout as _legacy
from motoetkinlik_source import discover_news, reference_snapshots

_EDITORIAL_DISCOVERY_URLS=set()

def turkish_web_scout(limit_per_source=120):
    rows=[];seen=set()
    for row in discover_news(limit_per_endpoint=min(limit_per_source,120)):
        title,url,series=row["title"],row["url"],row.get("series","")
        rider=_legacy.rider_for(title+" "+url,series or "MotoEtkinlik")
        if not rider or rider not in _legacy.RIDER_SOURCES or url in seen:
            continue
        if series not in ("MotoGP","Moto2","Moto3","WorldSBK","WorldSSP","WorldSSP300","WorldSPB","Moto4"):
            series=_legacy.RIDER_SOURCES[rider].get("series","")
        seen.add(url);rows.append((title,url,rider,series))
    # Preserve all non-MotoEtkinlik open-web sources. The legacy MotoEtkinlik
    # endpoints are filtered here so each verified category is requested once.
    original=_legacy.TURKISH_WEB_SOURCES
    try:
        _legacy.TURKISH_WEB_SOURCES=tuple(x for x in original if not x[0].startswith("MotoEtkinlik"))
        for item in _legacy.turkish_web_scout(limit_per_source):
            if item[1] not in seen:
                seen.add(item[1]);rows.append(item)
    finally:
        _legacy.TURKISH_WEB_SOURCES=original
    round2={row[1] for row in rows}
    if _EDITORIAL_DISCOVERY_URLS:
        only2=round2-_EDITORIAL_DISCOVERY_URLS
        overlap=round2&_EDITORIAL_DISCOVERY_URLS
        print(f"DISCOVERY-COMPARE round1={len(_EDITORIAL_DISCOVERY_URLS)} round2={len(round2)} overlap={len(overlap)} only_round2={len(only2)}")
        if only2:
            print("DISCOVERY-COMPARE only_round2_urls="+str(sorted(only2)[:20]))
    print(f"TURKISH WEB SCOUT + MOTOETKINLIK ADAPTER: {len(rows)} registered-rider candidates")
    return rows

def motoetkinlik_reference_data():
    return reference_snapshots()


def racing_editorial_scout(limit_per_source=120):
    """General Racing discovery over the same stable web sources as Turkish Rider.

    Unlike turkish_web_scout(), this lane deliberately does NOT require a registered
    Turkish rider. It only discovers candidates; article fetch, freshness, series,
    fact and QM gates remain downstream authorities.
    """
    rows=[];seen=set()
    valid=("MotoGP","Moto2","Moto3","WorldSBK","WorldSSP","WorldSSP300","WorldSPB","Moto4")
    for row in discover_news(limit_per_endpoint=min(limit_per_source,120)):
        title,url,series=row["title"],row["url"],row.get("series","")
        if url in seen:
            continue
        seen.add(url);rows.append((title,url,series if series in valid else "",row.get("source","MotoEtkinlik")))
    for source,base in _legacy.TURKISH_WEB_SOURCES:
        for title,url,series,_rider in _legacy._turkish_site_crawl(source,base,max_pages=30,depth=2):
            if url in seen:
                continue
            # The crawler already applies source-specific article routes. Keep only
            # racing-relevant candidates; unknown series is resolved from the article later.
            if _legacy.racing_relevance(title+" "+url)<=0:
                continue
            seen.add(url);rows.append((title,url,series if series in valid else "",source))
    global _EDITORIAL_DISCOVERY_URLS
    _EDITORIAL_DISCOVERY_URLS={row[1] for row in rows}
    print(f"RACING EDITORIAL SCOUT: {len(rows)} general candidates")
    print(f"DISCOVERY-SNAPSHOT round1_unique_urls={len(_EDITORIAL_DISCOVERY_URLS)}")
    return rows
