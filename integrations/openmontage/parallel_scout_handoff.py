"""Bounded parallel discovery handoff for agent 05.

YouTube/Instagram are additional evidence lanes, never prerequisites for
agent 05's independent research. Discovery URLs are not media licenses.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.parse import urlparse


def _clean(rows, lane, limit):
    cleaned = []
    for item in (rows or [])[:limit]:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        title = item.get("title", "")
        if not isinstance(url, str) or not isinstance(title, str):
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or not title.strip():
            continue
        cleaned.append({"lane": lane, "title": title[:300],
                        "url": url, "usage": "discovery_only",
                        "media_rights_verified": False})
    return cleaned


def collect_parallel_research(*, agent05, youtube, instagram, timeout=15, limit=20):
    """Collect independent search results without waiting on failed scouts.

    Callables are injected by runtime; this does not claim any platform API is
    already configured or bypass website access rules.
    """
    if not 1 <= timeout <= 60 or not 1 <= limit <= 50:
        raise ValueError("Invalid discovery bounds")

    pool = ThreadPoolExecutor(max_workers=3)
    try:
        jobs = {"agent05": pool.submit(agent05),
                "youtube": pool.submit(youtube),
                "instagram": pool.submit(instagram)}
        output = {}
        for lane, future in jobs.items():
            try:
                output[lane] = _clean(future.result(timeout=timeout), lane, limit)
            except Exception:
                output[lane] = []
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    return {"agent05": output["agent05"], "supplemental": (
        output["youtube"] + output["instagram"]),
        "scout_status": {lane: bool(output[lane]) for lane in jobs}}
