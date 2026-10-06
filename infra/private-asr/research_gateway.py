"""Provider-neutral bounded live-research gateway for Block 9.

The caller supplies only a search query. Providers are selected from already
configured infrastructure; no arbitrary URL fetch, shell, model, or secret is
accepted from a request.
"""
from __future__ import annotations
import os
from search_provider import _gemini_grounded, _search_searxng, _valid_searxng_url

MAX_QUERY=500
MAX_RESULTS=6

def research(query: str) -> dict:
    query=(query or "").strip()
    if not query or len(query)>MAX_QUERY:
        raise ValueError("invalid_query")

    configured=os.getenv("SEARXNG_URL","").strip()
    if configured:
        base=_valid_searxng_url(configured)
        if base:
            try:
                result=_search_searxng(query,base,MAX_RESULTS)
                return _bounded(result)
            except RuntimeError:
                pass

    key=os.getenv("GEMINI_API_KEY","").strip()
    if key:
        result=_gemini_grounded(query,key,None)
        if result and result.get("live_search") is True:
            return _bounded(result)

    return {"live_search":False,"provider":None,"results":[],
            "warning":"NO_LIVE_RESEARCH_PROVIDER_AVAILABLE"}

def _bounded(result: dict) -> dict:
    rows=[]
    for item in (result.get("results") or [])[:MAX_RESULTS]:
        if not isinstance(item,dict):
            continue
        url=str(item.get("url") or "")[:2048]
        if not url.startswith(("https://","http://")):
            continue
        rows.append({"title":str(item.get("title") or url)[:240],
                     "url":url,
                     "snippet":str(item.get("snippet") or "")[:800]})
    return {"live_search":bool(result.get("live_search")),
            "provider":str(result.get("provider") or "unknown")[:80],
            "results":rows,
            "warning":result.get("warning")}
