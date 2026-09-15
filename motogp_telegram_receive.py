"""Verarbeitet MotoGP-Freigaben; nur vollständig medienreife Sessions dürfen in die Publisher-Kette."""
from pathlib import Path
import re
from telegram_bot import get_chat_id, get_updates, send_message

SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md')
STATE=Path('memory/MOTOGP_APPROVAL_STATE.md')
PUBLISHED=Path('content/PUBLISHED.md')
MIN_SESSION_VERSION=2

def parse_session():
    if not SESSION.exists():
        print('DIAG: Keine MotoGP Approval Session vorhanden.'); return {}
    raw=SESSION.read_text(encoding='utf-8')
    vm=re.search(r'(?m)^Session-Version:\s*(\d+)\s*$',raw)
    version=int(vm.group(1)) if vm else 0
    if version<MIN_SESSION_VERSION:
        print(f'DIAG: Veraltete MotoGP Session-Version {version}; mindestens {MIN_SESSION_VERSION} erforderlich.'); return {}
    posts={}
    for m in re.finditer(r'(?ms)^## Beitrag\s+([1-3])\s*$\n(.*?)(?=^## Beitrag\s+[1-3]\s*$|\Z)',raw):
        n=int(m.group(1)); sec=m.group(2)
        def f(name):
            x=re.search(rf'(?m)^{re.escape(name)}:\s*(.*)$',sec); return x.group(1).strip() if x else ''
        tm=re.search(r'(?ms)^Text:\s*(.*?)(?=^\s*Rechte-Gate:)',sec)
        post={'title':f('Titel'),'source':f('Quelle'),'image':f('Instagram-Bild'),'text':tm.group(1).strip() if tm else ''}
        if not post['image'] or post['image'].lower()=='auto' or not Path(post['image']).exists():
            print(f'DIAG: Beitrag {n} nicht medienreif: Instagram-Bild fehlt.'); continue
        if any(x.casefold() in post['text'].casefold() for x in ('-->','By motogp.com','MotoGP-Update:')):
            print(f'DIAG: Beitrag {n} wegen veraltetem Rohtext gesperrt.'); continue
        posts[n]=post
    print(f'DIAG: {len(posts)} medienreife Beiträge aus Approval Session geladen.'); return posts

def selection(text):
    v=re.sub(r'\s+',' ',text.strip().lower())
    if v in ('motogp alle','motogp ✅'): return [1,2,3]
    if v in ('motogp nein','motogp ❌'): return []
    m=re.fullmatch(r'motogp\s+([1-3](?:\s*,\s*[1-3])*)',v)
    return sorted({int(x.strip()) for x in m.group(1).split(',')}) if m else None

def already(update_id):
    return STATE.exists() and f'Update-ID: {update_id}' in STATE.read_text(encoding='utf-8')

def publish(posts,chosen,update_id):
    existing=PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n'; blocks=[]
    for n in chosen:
        p=posts.get(n)
        if not p: continue
        marker=f'Telegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}'
        if marker in existing: continue
        blocks.append(f'## Instagram\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\nQuelle: {p["source"]}\nMedienstatus: EIGENE_KI_EDITORIALGRAFIK\nBild: {p["image"]}\n')
        blocks.append(f'## Facebook\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n')
    if blocks:
        PUBLISHED.parent.mkdir(parents=True,exist_ok=True); PUBLISHED.write_text(existing.rstrip()+'\n\n'+'\n'.join(blocks).rstrip()+'\n',encoding='utf-8')
        print(f'DIAG: {len(blocks)} medienreife Plattform-Blöcke übergeben.')

def main():
    allowed=str(get_chat_id()); posts=parse_session()
    updates=get_updates(); handled=False
    for upd in sorted(updates,key=lambda x:x.get('update_id',0)):
        uid=upd.get('update_id'); msg=upd.get('message') or {}; chat=str((msg.get('chat') or {}).get('id','')); txt=msg.get('text')
        if not isinstance(uid,int) or not isinstance(txt,str): continue
        chosen=selection(txt)
        if chosen is None or chat!=allowed or already(uid): continue
        if chosen and (not posts or any(n not in posts for n in chosen)):
            send_message('⛔ Diese MotoGP-Auswahl ist veraltet oder noch nicht medienreif und wird nicht veröffentlicht. Bitte die neue Tagesauswahl verwenden.')
        elif chosen:
            publish(posts,chosen,uid); send_message(f'✅ MotoGP: {len(chosen)} Content-Paket(e) freigegeben. Instagram-Medium ist bereits vorbereitet; Facebook nutzt die offizielle Link-Vorschau.')
        else:
            send_message('❌ MotoGP-Tagesauswahl verworfen. Es wird nichts veröffentlicht.')
        STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(f'Update-ID: {uid}\nAntwort: {txt}\n',encoding='utf-8'); handled=True
    if not handled: print('DIAG: Kein neues gültiges MotoGP-Freigabekommando gefunden.')

if __name__=='__main__': main()
