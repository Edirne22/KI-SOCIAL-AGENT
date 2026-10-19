"""Agent Reach subprocess boundary; disabled until explicit runtime provisioning.

Agent Reach is an installer/doctor for upstream tools, not an autonomous
fact-checker. Avoid automatic package installs and implicit login/cookie access.
"""
from __future__ import annotations
import hashlib
import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from urllib.parse import urlsplit, quote
from urllib.request import Request, urlopen

from integrations.openmontage.motorsport_source_catalog import SOURCES

logger = logging.getLogger(__name__)

NEWS_HOSTS = set()
for s in SOURCES:
    if s.get('name') in ('MotoGP', 'WorldSBK', 'TRF1', 'MotoEtkinlik', 'MotoGP results'):
        host = urlsplit(s['url']).hostname
        if host:
            NEWS_HOSTS.add(host)
            if host.startswith('www.'):
                NEWS_HOSTS.add(host[4:])
            else:
                NEWS_HOSTS.add('www.' + host)


def fold_text(text: str) -> str:
    """Normalize Turkish and special characters to standard lowercase ASCII."""
    if not text:
        return ""
    table = str.maketrans({
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'I': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u',
    })
    return text.translate(table).casefold()


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
    installed_version = None
    try:
        installed_version = version('agent-reach')
    except Exception as exc:
        logger.warning(f"agent-reach package check failed: {exc}")

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


def topic_terms(topic):
    """Find meaningful subject words; ignore generic production instructions."""
    stop = {'aktuelle', 'aktuell', 'überprüfbare', 'uberprufbare', 'nachrichten', 'news',
            'deutsch', 'deutsche', 'motorrad', 'film', 'video', 'erstelle',
            'erstellen', 'bitte', 'über', 'uber', 'und', 'der', 'die', 'das', 'für', 'fur',
            'auf', 'mit', 'zum', 'eine', 'einen', 'sekunden', 'reels', 'szene', 'szenen'}
    folded = fold_text(topic)
    return [word for word in re.findall(r'[^\W_]{3,}', folded)
            if word not in stop][:6]


def discover(topic):
    """Live catalog discovery, never a fixed article or a search snippet as proof."""
    terms = topic_terms(topic)
    if not terms:
        return {'results': [], 'errors': [{'error': 'NO_SEARCH_SUBJECT'}]}
    listings = [
        'https://trf1.net/?s=' + quote(terms[0]),
        'https://www.motogp.com/en/news',
        'https://www.worldsbk.com/en/news',
        'https://motoetkinlik.com/',
    ]
    candidates, errors = {}, []
    for url in listings:
        try:
            page = read_web(url)
            pattern = (r'^### \[([^\]\n]+)\]\((https://[^\s)]+)'
                       if '?s=' in url else r'\[([^\]\n]+)\]\((https://[^\s)]+)')
            for label, link in re.findall(pattern, page['text'], re.M):
                link = link.rstrip('"')
                try:
                    validate_news_url(link)
                except ValueError:
                    continue
                folded_candidate = fold_text(label + ' ' + link)
                topical = any(w in folded_candidate for w in terms)
                official_article = '/en/news/20' in link
                if topical or official_article:
                    if any(s in link for s in ('/uploads/', '/riders/', '/tag/')):
                        continue
                    candidates.setdefault(link, {'url': link, 'title': label,
                                                 'topical': topical, 'discovery_url': url})
        except Exception as exc:
            logger.warning(f"Discovery failed for {url}: {exc}")
            errors.append({'url': url, 'error': type(exc).__name__, 'detail': str(exc)})
    ranked = sorted(candidates.values(), key=lambda c: not c['topical'])
    selected, counts = [], {}
    for candidate in ranked:
        host = urlsplit(candidate['url']).hostname
        limit = 6 if host in ('www.motogp.com', 'motogp.com', 'trf1.net', 'www.trf1.net') else 3
        if counts.get(host, 0) < limit:
            selected.append(candidate)
            counts[host] = counts.get(host, 0) + 1
    return {'results': selected[:12], 'errors': errors}


def availability() -> dict:
    binary = shutil.which("agent-reach")
    has_pkg = False
    try:
        version('agent-reach')
        has_pkg = True
    except Exception:
        pass
    installed = bool(binary or has_pkg)
    return {"installed": installed, "executable": binary, "enabled": installed}


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
