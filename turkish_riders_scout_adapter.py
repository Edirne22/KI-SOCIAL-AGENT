"""Compatibility facade: existing Turkish scout plus dedicated MotoEtkinlik discovery."""
from turkish_riders_scout import *  # noqa: F401,F403
import turkish_riders_scout as _legacy
from motoetkinlik_source import discover_news, reference_snapshots

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
    print(f"TURKISH WEB SCOUT + MOTOETKINLIK ADAPTER: {len(rows)} registered-rider candidates")
    return rows

def motoetkinlik_reference_data():
    return reference_snapshots()
