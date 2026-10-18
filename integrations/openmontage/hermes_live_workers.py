"""Wire existing OpenMontage research to fail-closed coordinator (research only).

No production dispatch, publishing, installation, or secret access.
"""
from __future__ import annotations
from urllib.parse import urlsplit
import requests
from integrations.openmontage.hermes_coordinator import run_research
from scripts.openmontage_agent05_oncu_live import research, _nemotron_assess

def _discovery(state):
    result = research(state["topic"])
    topic = state["topic"].casefold()
    terms = [x for x in ("michelin", "power gp", "öncü", "oncu", "motogp", "worldsbk") if x in topic]
    candidates = [r for r in result.get("results", []) if
                  any(t in (str(r.get("title", ""))+" "+str(r.get("url", ""))).casefold() for t in terms)]
    return {"candidates": candidates}

def _reader(state):
    docs = []
    for candidate in state["research_discovery"]["candidates"][:5]:
        url = str(candidate.get("url") or "")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            continue
        try:
            response = requests.get(url, timeout=(5, 12), headers={"User-Agent": "OpenMontageResearch/1.0"})
            response.raise_for_status()
            from html.parser import HTMLParser
            class Extract(HTMLParser):
                def __init__(self):
                    super().__init__(); self.parts=[]; self.ignore=0
                def handle_starttag(self, tag, attrs):
                    if tag in ("script","style","nav","footer"): self.ignore+=1
                def handle_endtag(self, tag):
                    if tag in ("script","style","nav","footer") and self.ignore: self.ignore-=1
                def handle_data(self, data):
                    if not self.ignore and data.strip(): self.parts.append(data.strip())
            parser=Extract(); parser.feed(response.text[:300000])
            text=" ".join(parser.parts)[:15000]
            if len(text)>250:
                docs.append({"url":response.url,"text":text,"candidate_title":candidate.get("title","")})
        except (requests.RequestException, ValueError):
            continue
    return {"documents":docs}

def _analyst(state):
    # Nemotron assessment is advisory and must never become an evidence claim.
    documents=state["source_reader"]["documents"]
    result=_nemotron_assess([{"title":d["candidate_title"],"url":d["url"]} for d in documents])
    return {"assessment":result, "claims": []}

def _checker(state):
    # Fail closed until source-text-grounded structured claims are implemented.
    return {"verified_claims":[]}

def _handoff(state):
    return {"report":"Not reachable without verified claims"}

def run(topic: str) -> dict:
    return run_research(topic, {
        "research_discovery": _discovery,
        "source_reader": _reader,
        "nemotron_analyst": _analyst,
        "fact_checker": _checker,
        "handoff": _handoff,
    }, max_retries=0)
