"""Verarbeitet Racing-Freigaben für fünf Chief-QM-geprüfte Pakete."""
from pathlib import Path
import re,sys
from telegram_bot import get_chat_id,get_updates,send_message
SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md');STATE=Path('memory/MOTOGP_APPROVAL_STATE.md');PUBLISHED=Path('content/PUBLISHED.md');MIN_SESSION_VERSION=8
RAW_BAD=('-->','by motogp.com','motogp-update:','eines der relevanten motogp-themen','die fakten stammen aus der offiziellen meldung')
def parse_session():
    if not SESSION.exists():return {}
    raw=SESSION.read_text(encoding='utf-8');vm=re.search(r'(?m)^Session-Version:\s*(\d+)\s*$',raw);version=int(vm.group(1)) if vm else 0
    if version<MIN_SESSION_VERSION or not re.search(r'(?m)^QM:\s*PASS\s*$',raw):return {}
    posts={}
    for m in re.finditer(r'(?ms)^## Beitrag\s+([1-5])\s*$\n(.*?)(?=^## Beitrag\s+[1-5]\s*$|\Z)',raw):
        n=int(m.group(1));sec=m.group(2)
        def f(name):
            x=re.search(rf'(?m)^{re.escape(name)}:\s*(.*)$',sec);return x.group(1).strip() if x else ''
        tm=re.search(r'(?ms)^Text:\s*(.*?)(?=^\s*Rechte-Gate:)',sec);post={'title':f('Titel'),'source':f('Quelle'),'image':f('Instagram-Bild'),'text':tm.group(1).strip() if tm else ''}
        low=post['text'].casefold()
        if not re.search(r'(?m)^QM:\s*PASS\s*$',sec) or any(x in low for x in RAW_BAD):continue
        if not post['source'].startswith('http') or not post['image'] or post['image'].lower()=='auto' or not Path(post['image']).is_file():continue
        posts[n]=post
    return posts
def selection(text):
    v=re.sub(r'\s+',' ',text.strip().lower())
    if v in ('motogp alle','motogp ✅'):return [1,2,3,4,5]
    if v in ('motogp nein','motogp ❌'):return []
    m=re.fullmatch(r'motogp\s+([1-5](?:\s*,\s*[1-5])*)',v);return sorted({int(x.strip()) for x in m.group(1).split(',')}) if m else None
def already(uid):return STATE.exists() and f'Update-ID: {uid}' in STATE.read_text(encoding='utf-8')
def publish(posts,chosen,uid):
    PUBLISHED.parent.mkdir(parents=True,exist_ok=True);existing=PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n';blocks=[]
    for n in chosen:
        p=posts.get(n)
        if not p:continue
        marker=f'Telegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}'
        if marker in existing:continue
        blocks += [f'## Instagram\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\nQuelle: {p["source"]}\nMedienstatus: EIGENE_KI_EDITORIALGRAFIK\nBild: {p["image"]}\n',f'## Facebook\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n']
    if blocks:PUBLISHED.write_text(existing.rstrip()+'\n\n'+'\n'.join(blocks).rstrip()+'\n',encoding='utf-8')
    return len(blocks)
def handle_one(uid,chat,txt):
    if chat!=str(get_chat_id()) or already(uid):return False
    chosen=selection(txt)
    if chosen is None:return False
    posts=parse_session()
    if chosen and (len(posts)!=5 or any(n not in posts for n in chosen)):send_message('⛔ Auswahl veraltet oder nicht vollständig Chief-QM-geprüft. Nichts veröffentlicht.')
    elif chosen:send_message(f'✅ Racing: {len(chosen)} Content-Paket(e) freigegeben. {publish(posts,chosen,uid)} Plattform-Blöcke wurden übergeben.')
    else:send_message('❌ Tagesauswahl verworfen. Es wird nichts veröffentlicht.')
    STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(f'Update-ID: {uid}\nAntwort: {txt}\n',encoding='utf-8');return True
def main():
    if len(sys.argv)>=4:
        if not handle_one(int(sys.argv[1]),sys.argv[2],sys.argv[3]):raise SystemExit(2)
        return
    for upd in sorted(get_updates(),key=lambda x:x.get('update_id',0)):
        uid=upd.get('update_id');msg=upd.get('message') or {};txt=msg.get('text');chat=str((msg.get('chat') or {}).get('id',''))
        if isinstance(uid,int) and isinstance(txt,str) and selection(txt) is not None:handle_one(uid,chat,txt)
if __name__=='__main__':main()
