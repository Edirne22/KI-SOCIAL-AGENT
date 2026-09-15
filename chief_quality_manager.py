"""Zentrale, fail-closed End-QM-Schicht für KI-SOCIAL-AGENT."""
from pathlib import Path
from datetime import datetime, timezone
import re

LOG=Path('memory/QUALITY_MANAGER_LOG.md')

def _log(domain,item,ok,errors):
    LOG.parent.mkdir(parents=True,exist_ok=True)
    old=LOG.read_text(encoding='utf-8') if LOG.exists() else '# Chief Quality Manager Log\n\n'
    title=item.get('title','ohne Titel')
    state='PASS' if ok else 'FAIL'
    row=f'## {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} | {domain} | {state}\nTitel: {title}\nStory-Key: {item.get("story_key","")}\nGründe: {"; ".join(errors) if errors else "alle Gates bestanden"}\n\n'
    LOG.write_text(old+row,encoding='utf-8')

def review(domain,item,caption,media_path='',source_url='',domain_reviewer=None):
    errors=[]; low=(caption or '').casefold()
    if not caption.strip(): errors.append('Copy fehlt')
    if not source_url.startswith('http'): errors.append('belastbare Quelle fehlt')
    if not media_path or media_path.strip().casefold()=='auto': errors.append('publishbares Medium fehlt')
    if any(x in low for x in ('social-text','redaktion','die fakten stammen aus der offiziellen meldung','eines der relevanten')):
        errors.append('interne/generische Meta-Sprache')
    if '?' not in caption: errors.append('Community-Frage fehlt')
    if len(re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption)) < 3: errors.append('zu wenige relevante Hashtags')
    if domain_reviewer:
        ok,domain_errors=domain_reviewer(item,caption)
        if not ok: errors.extend('Domain-QM: '+e for e in domain_errors)
    ok=not errors
    _log(domain,item,ok,errors)
    return ok,errors

def review_batch(domain,items,domain_reviewer=None):
    results=[]; seen=set()
    for item in items:
        caption=item.get('caption','')
        fp=re.sub(r'#[^\s]+','',caption.casefold()); fp=re.sub(r'\s+',' ',fp).strip()
        ok,errors=review(domain,item,caption,item.get('instagram_media',''),item.get('url',''),domain_reviewer)
        if fp in seen:
            ok=False; errors=errors+['Copy-Duplikat im Batch']
            _log(domain,item,False,['Copy-Duplikat im Batch'])
        seen.add(fp); results.append((ok,errors))
    return results
