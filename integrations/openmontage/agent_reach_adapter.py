"""Agent Reach subprocess boundary; disabled until explicit runtime provisioning.

Agent Reach is an installer/doctor for upstream tools, not an autonomous
fact-checker. Avoid automatic package installs and implicit login/cookie access.
"""
from __future__ import annotations
import shutil
import subprocess
import hashlib
import re
from datetime import datetime, timezone
from importlib.metadata import version
from urllib.parse import urlsplit, quote
from urllib.request import Request, urlopen

from integrations.openmontage.motorsport_source_catalog import SOURCES

NEWS_HOSTS = {urlsplit(s['url']).hostname for s in SOURCES
              if s['name'] in ('MotoGP', 'WorldSBK', 'TRF1', 'MotoEtkinlik')}


def validate_news_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.hostname not in NEWS_HOSTS or p.username
            or p.password or p.port not in (None, 443) or p.fragment
            or any(c in url for c in ('\n', '\r', '\\'))):
        raise ValueError('Unapproved research URL')
    return url


def read_web(url):
    """Agent Reach's documented Web backend: Jina Reader, no key/cookies."""
    validate_news_url(url)
    installed_version = version('agent-reach')  # fail if runtime not provisioned
    req = Request('https://r.jina.ai/' + url,
                  headers={'User-Agent': 'KI-SOCIAL-AGENT-Research/1.0'})
    with urlopen(req, timeout=40) as response:
        raw = response.read(300001)
        if response.status != 200 or len(raw) > 300000:
            raise ValueError('Research response failed or too large')
    text = raw.decode('utf-8')
    if len(text) < 200 or 'Markdown Content:' not in text:
        raise ValueError('Jina article content missing')
    return {'url': url, 'text': text, 'backend': 'agent-reach/web/jina',
            'agent_reach_version': installed_version,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(raw).hexdigest()}


def discover(topic):
    """Live catalog discovery, never a fixed article or a search snippet as proof."""
    listings = ['https://trf1.net/?s=' + quote(topic),
                'https://www.motogp.com/en/news',
                'https://www.worldsbk.com/en/news']
    candidates, errors = {}, []
    for url in listings:
        try:
            page = read_web(url)
            for label, link in re.findall(r'\[([^\]\n]+)\]\((https://[^\s)]+)', page['text']):
                link = link.rstrip('"')
                try:
                    validate_news_url(link)
                except ValueError:
                    continue
                subject_terms = [w for w in re.findall(r'[^\W_]{3,}', topic.casefold())
                                 if w not in {'aktuelle', 'überprüfbare', 'news', 'deutsch', 'motorrad', 'und', 'der', 'die', 'das', 'über'}]
                topical = any(w in (label + ' ' + link).casefold() for w in subject_terms)
                official_article = '/en/news/20' in link
                if topical or official_article:
                    if any(s in link for s in ('/uploads/', '/riders/', '/tag/')):
                        continue
                    candidates.setdefault(link, {'url': link, 'title': label,
                                                 'topical': topical, 'discovery_url': url})
        except Exception as exc:
            errors.append({'url': url, 'error': type(exc).__name__})
    ranked = sorted(candidates.values(), key=lambda c: not c['topical'])
    selected, counts = [], {}
    for candidate in ranked:
        host = urlsplit(candidate['url']).hostname
        limit = 6 if host == 'www.motogp.com' else 3
        if counts.get(host, 0) < limit:
            selected.append(candidate)
            counts[host] = counts.get(host, 0) + 1
    return {'results': selected[:12], 'errors': errors}

def availability() -> dict:
    binary = shutil.which("agent-reach")
    return {"installed": bool(binary), "executable": binary, "enabled": False}

def doctor(timeout: int = 20) -> dict:
    binary = shutil.which("agent-reach")
    if not binary:
        return {"status": "UNAVAILABLE", "reason": "AGENT_REACH_NOT_INSTALLED"}
    try:
        result = subprocess.run([binary, "doctor"], capture_output=True,
                                text=True, timeout=timeout, check=False)
        return {"status": "OK" if result.returncode == 0 else "DEGRADED",
                "exit_code": result.returncode}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "UNAVAILABLE", "reason": "DOCTOR_FAILED"}
