"""V8.5 human approval gate for Racing. QA PASS is never equal to human approval."""
from pathlib import Path
import re,sys,time
from telegram_bot import get_chat_id,get_updates,send_message
import racing_run_controller as rc
SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md');STATE=Path('memory/MOTOGP_APPROVAL_STATE.md');PUBLISHED=Path('content/PUBLISHED.md')
MIN_SESSION_VERSION=18;MAX_SESSION_AGE_SECONDS=24*3600
RAW_BAD=('-->','by motogp.com','motogp-update:','eines der relevanten motogp-themen','die fakten stammen aus der offiziellen meldung')
def _active_batch():
    try:return rc._load().get('active_batch_id','')
    except Exception:return ''
def parse_session():
    if not SESSION.exists():return {}
    raw=SESSION.read_text(encoding='utf-8');vm=re.search(r'(?m)^Session-Version:\s*(\d+)\s*$',raw);version=int(vm.group(1)) if vm else 0
    if version<MIN_SESSION_VERSION:return {}
    if not re.search(r'(?m)^Approval-Status:\s*READY\s*$',raw) or not re.search(r'(?m)^QM:\s*PASS\s*$',raw):return {}
    tm=re.search(r'(?m)^Session-Timestamp:\s*(\d+)\s*$',raw)
    if not tm:return {}
    try:age=int(time.time())-int(tm.group(1))
    except Exception:return {}
    if age < -300 or age > MAX_SESSION_AGE_SECONDS:return {}
    posts={}
    for m in re.finditer(r'(?ms)^## Beitrag\s+([1-5])\s*$\n(.*?)(?=^## Beitrag\s+[1-5]\s*$|\Z)',raw):
        n=int(m.group(1));sec=m.group(2)
        def f(name):
            x=re.search(rf'(?m)^{re.escape(name)}:\s*(.*)$',sec);return x.group(1).strip() if x else ''
        tx=re.search(r'(?ms)^Text:\s*(.*?)(?=^\s*Rechte-Gate:)',sec);post={'title':f('Titel'),'source':f('Quelle'),'image':f('Instagram-Bild'),'text':tx.group(1).strip() if tx else ''}
        low=post['text'].casefold()
        gates=('QM','Racing-QM','Semantic-Fakten-QM')
        if any(not re.search(rf'(?m)^{re.escape(g)}:\s*PASS\s*$',sec) for g in gates):continue
        if any(x in low for x in RAW_BAD):continue
        if not post['source'].startswith('http') or not post['image'] or post['image'].lower()=='auto' or not Path(post['image']).is_file():continue
        posts[n]=post
    return posts if len(posts)==5 else {}
def selection(text):
    v=re.sub(r'\s+',' ',text.strip().lower())
    if v in ('motogp alle','motogp ✅'):return [1,2,3,4,5]
    if v in ('motogp nein','motogp ❌'):return []
    m=re.fullmatch(r'motogp\s+([1-5](?:\s*,\s*[1-5])*)',v);return sorted({int(x.strip()) for x in m.group(1).split(',')}) if m else None
def already(uid):return STATE.exists() and f'Update-ID: {uid}' in STATE.read_text(encoding='utf-8')
def _normalize_text(t):return re.sub(r'\s+',' ',t.strip()).casefold()
def get_existing_published_texts():
    texts=set();files=[PUBLISHED]
    archive_dir=PUBLISHED.parent/'archive'
    if archive_dir.exists():files.extend(archive_dir.glob('*.md'))
    pattern=r'(?ms)^Text:\s*(.*?)(?=^(?:Quelle:|Bild:|Video:|Bilder:|Medienstatus:|Link-Preview:|Status:|Freigabe:|Telegram-Update-ID:|Racing-Batch-ID:|MotoGP-Auswahl:|Titel:|## |\Z))'
    for f in files:
        if not f.exists():continue
        content=f.read_text(encoding='utf-8')
        for m in re.findall(pattern,content):
            norm=_normalize_text(m)
            if norm:texts.add(norm)
    return texts
def publish(posts,chosen,uid,batch):
    PUBLISHED.parent.mkdir(parents=True,exist_ok=True);existing=PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n';blocks=[]
    existing_texts=get_existing_published_texts()
    for n in chosen:
        p=posts.get(n)
        if not p:continue
        marker=f'Racing-Batch-ID: {batch}\nMotoGP-Auswahl: {n}'
        if marker in existing:continue
        norm_post_text=_normalize_text(p["text"])
        if norm_post_text and norm_post_text in existing_texts:
            print(f"DUPLIKAT ERKANNT: {p['title']} bereits vorhanden, übersprungen")
            continue
        if norm_post_text:existing_texts.add(norm_post_text)
        common=f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\nRacing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        blocks += [f'## Instagram\n{common}Text:\n{p["text"]}\nQuelle: {p["source"]}\nMedienstatus: EIGENE_KI_EDITORIALGRAFIK\nBild: {p["image"]}\n',f'## Facebook\n{common}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n']
    if blocks:PUBLISHED.write_text(existing.rstrip()+'\n\n'+'\n'.join(blocks).rstrip()+'\n',encoding='utf-8')
    return len(blocks)
def handle_one(uid,chat,txt):
    if chat!=str(get_chat_id()) or already(uid):return False
    chosen=selection(txt)
    if chosen is None:return False
    batch=_active_batch();run=rc.get_run(batch) if batch else {}
    posts=parse_session()
    if chosen:
        if run.get('status')!='READY_FOR_APPROVAL' or len(posts)!=5 or any(n not in posts for n in chosen):send_message('⛔ Auswahl veraltet, bereits geschlossen oder nicht vollständig Chief-QM-geprüft. Nichts veröffentlicht.')
        else:
            rc.transition(batch,'APPROVED',telegram_update_id=uid,selection=chosen);count=publish(posts,chosen,uid,batch);rc.transition(batch,'PUBLISHED',platform_blocks=count);send_message(f'✅ Racing {batch}: {len(chosen)} Content-Paket(e) freigegeben. {count} Plattform-Blöcke wurden übergeben.')
    else:
        if batch:rc.transition(batch,'CLOSED',decision='rejected_by_human')
        send_message('❌ Tagesauswahl verworfen. Es wird nichts veröffentlicht.')
    STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(f'Update-ID: {uid}\nRacing-Batch-ID: {batch}\nAntwort: {txt}\n',encoding='utf-8');return True
def main():
    if len(sys.argv)>=4:
        if not handle_one(int(sys.argv[1]),sys.argv[2],sys.argv[3]):raise SystemExit(2)
        return
    for upd in sorted(get_updates(),key=lambda x:x.get('update_id',0)):
        uid=upd.get('update_id');msg=upd.get('message') or {};txt=msg.get('text');chat=str((msg.get('chat') or {}).get('id',''))
        if isinstance(uid,int) and isinstance(txt,str) and selection(txt) is not None:handle_one(uid,chat,txt)
if __name__=='__main__':main()
