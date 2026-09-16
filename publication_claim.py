"""Reserviert genau einen freigegebenen Beitrag vor einer externen Veröffentlichung.

Die Reservierung wird vor dem Plattform-Aufruf nach Git gepusht. So verhindert das
System einen Doppelpost, wenn ein späterer Plattform- oder Git-Schritt unklar
abbricht. Ein hängen gebliebener Claim wird niemals automatisch erneut gesendet.
"""
from __future__ import annotations
import argparse,re
from datetime import datetime,timezone
from pathlib import Path
from media_policy import media_publishable
PUBLISHED=Path('content/PUBLISHED.md');DUPLICATES=Path('memory/PUBLICATION_DUPLICATES.md')
CLAIM_READY='Publication-Claim: BEREIT';CLAIM_ACTIVE='Publication-Claim: IN_BEARBEITUNG'
TARGETS={'instagram':r'Instagram','story':r'Story','reel':r'(?:Instagram Reel|Reel)','facebook':r'Facebook','instagram-carousel':r'Instagram Karussell','facebook-carousel':r'Facebook Karussell'}
def _blocks(content,target):
    return list(re.compile(rf'(^## {TARGETS[target]}\s*\n.*?)(?=^## |\Z)',re.MULTILINE|re.DOTALL).finditer(content))
def _real_media(block,kind):
    return bool(re.search(rf'(?mi)^{kind}:\s*(?!auto\s*$)\S+',block))
def _is_publishable(block,target):
    if '[GEPOSTET' in block or CLAIM_READY in block or CLAIM_ACTIVE in block or not re.search(r'(?mi)^Status:\s*FREIGEGEBEN\s*$',block):return False
    # Facebook may intentionally be a text/link post. Other formats need resolved media.
    if target=='facebook':
        if not re.search(r'(?ms)^Text:\s*\S+',block):return False
        has_media=_real_media(block,'Bild') or _real_media(block,'Video')
        has_link=bool(re.search(r'(?mi)^Quelle:\s*https?://\S+',block) and re.search(r'(?mi)^Link-Preview:\s*offiziell\s*$',block))
        if not (has_media or has_link):return False
    elif target=='instagram':
        if not _real_media(block,'Bild'):return False
    elif target=='story':
        if not (_real_media(block,'Bild') or _real_media(block,'Video')):return False
    elif target=='reel':
        if not _real_media(block,'Video'):return False
    else:
        images=re.findall(r'(?mi)^\s*-\s*(\S+)',block)
        if len(images)<2:return False
    if target in {'story','reel'} and re.search(r'(?mi)^Musik:\s*auto\s*$',block):return False
    allowed,reason=media_publishable(block)
    if not allowed:print(reason)
    return allowed
def _text_key(block):
    m=re.search(r'(?ms)^Text:\s*(.*?)(?=^(?:Bild|Video|Bilder|Freigabe|Status|Publication-Claim|Quelle|Medienstatus|Link-Preview):|\Z)',block)
    return re.sub(r'\s+',' ',m.group(1).strip().lower()) if m else ''
def _write_duplicates(target,texts):
    if not texts:return
    DUPLICATES.parent.mkdir(parents=True,exist_ok=True);old=DUPLICATES.read_text(encoding='utf-8') if DUPLICATES.exists() else '# Veröffentlichungs-Duplikate\n'
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC');lines=[f'\n## {stamp} – {target}','- Status: NICHT automatisch veröffentlicht','- Grund: Mehrere veröffentlichungsreife, freigegebene Blöcke haben denselben Text.','']
    lines += [f'- Duplikat {i}: {t[:180]}' for i,t in enumerate(texts,1)]
    DUPLICATES.write_text(old.rstrip()+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')
def claim(target):
    if not PUBLISHED.exists():print('PUBLISHED.md nicht gefunden – keine Reservierung angelegt.');return False
    content=PUBLISHED.read_text(encoding='utf-8')
    # Only publishable blocks participate in duplicate detection. Drafts with Bild/Video:auto
    # must never block a finished approved post with the same caption.
    eligible=[m.group(1) for m in _blocks(content,target) if _is_publishable(m.group(1),target)]
    keys=[_text_key(b) for b in eligible];duplicate_keys={k for k in keys if k and keys.count(k)>1}
    if duplicate_keys:_write_duplicates(target,sorted(duplicate_keys))
    for m in _blocks(content,target):
        block=m.group(1)
        if not _is_publishable(block,target):continue
        if _text_key(block) in duplicate_keys:print(f'{target}: Duplikat erkannt – nicht automatisch reserviert.');continue
        updated=re.sub(r'(?mi)^(Status:\s*FREIGEGEBEN\s*)$',rf'\1\n{CLAIM_READY}',block,count=1)
        PUBLISHED.write_text(content[:m.start()]+updated+content[m.end():],encoding='utf-8');print(f'Reserviert für Veröffentlichung: {target}.');return True
    print(f'Kein freigegebener, unreservierter {target}-Block gefunden.');return False
def start(target,token):
    if not PUBLISHED.exists():return False
    content=PUBLISHED.read_text(encoding='utf-8')
    for m in _blocks(content,target):
        block=m.group(1)
        if CLAIM_READY not in block or CLAIM_ACTIVE in block:continue
        updated=block.replace(CLAIM_READY,f'{CLAIM_ACTIVE} {token}',1);PUBLISHED.write_text(content[:m.start()]+updated+content[m.end():],encoding='utf-8');print(f'Veröffentlichung gestartet: {target}.');return True
    print(f'Kein bereiter {target}-Claim gefunden.');return False
def main():
    p=argparse.ArgumentParser();p.add_argument('--platform',choices=sorted(TARGETS),required=True);a=p.add_mutually_exclusive_group(required=True);a.add_argument('--claim',action='store_true');a.add_argument('--start',action='store_true');p.add_argument('--token');x=p.parse_args()
    if x.start and not x.token:p.error('--start benötigt --token')
    claim(x.platform) if x.claim else start(x.platform,x.token)
if __name__=='__main__':main()
