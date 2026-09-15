"""Verarbeitet ausschließlich MotoGP-Freigaben aus Telegram und übergibt sie an die bestehende Publisher-Kette."""
from pathlib import Path
import re
from telegram_bot import get_chat_id, get_updates, send_message

SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md')
STATE=Path('memory/MOTOGP_APPROVAL_STATE.md')
PUBLISHED=Path('content/PUBLISHED.md')

def parse_session():
    if not SESSION.exists():
        print('DIAG: Keine MotoGP Approval Session vorhanden.')
        return {}
    raw=SESSION.read_text(encoding='utf-8'); posts={}
    for m in re.finditer(r'(?ms)^## Beitrag\s+([1-3])\s*$\n(.*?)(?=^## Beitrag\s+[1-3]\s*$|\Z)',raw):
        n=int(m.group(1)); sec=m.group(2)
        def f(name):
            x=re.search(rf'(?m)^{re.escape(name)}:\s*(.*)$',sec)
            return x.group(1).strip() if x else ''
        tm=re.search(r'(?ms)^Text:\s*(.*?)(?=^\s*Rechte-Gate:)',sec)
        posts[n]={'title':f('Titel'),'source':f('Quelle'),'text':tm.group(1).strip() if tm else ''}
    print(f'DIAG: {len(posts)} Beiträge aus Approval Session geladen.')
    return posts

def selection(text):
    v=re.sub(r'\s+',' ',text.strip().lower())
    if v in ('motogp alle','motogp ✅'): return [1,2,3]
    if v in ('motogp nein','motogp ❌'): return []
    m=re.fullmatch(r'motogp\s+([1-3](?:\s*,\s*[1-3])*)',v)
    return sorted({int(x.strip()) for x in m.group(1).split(',')}) if m else None

def already(update_id):
    return STATE.exists() and f'Update-ID: {update_id}' in STATE.read_text(encoding='utf-8')

def publish(posts,chosen,update_id):
    existing=PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n'
    blocks=[]
    # Beide Plattformblöcke gemeinsam erzeugen; keine globale Quellenprüfung, die Facebook versehentlich überspringt.
    for n in chosen:
        p=posts.get(n)
        if not p: continue
        marker=f'Telegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}'
        if marker in existing:
            print(f'DIAG: Beitrag {n} für Update {update_id} bereits vorhanden; übersprungen.')
            continue
        blocks.append(f'## Instagram\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\nQuelle: {p["source"]}\nBild: auto\n')
        blocks.append(f'## Facebook\nStatus: FREIGEGEBEN\nFreigabe: Telegram MotoGP\nTelegram-Update-ID: {update_id}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\nText:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n')
    if blocks:
        PUBLISHED.parent.mkdir(parents=True,exist_ok=True)
        PUBLISHED.write_text(existing.rstrip()+'\n\n'+'\n'.join(blocks).rstrip()+'\n',encoding='utf-8')
        print(f'DIAG: {len(blocks)} Plattform-Blöcke an Publisher-Plan übergeben.')

def main():
    allowed=str(get_chat_id()); posts=parse_session()
    if not posts: return
    updates=get_updates()
    print(f'DIAG: Telegram lieferte {len(updates)} Update(s); erlaubter Chat ist konfiguriert.')
    handled=False
    for upd in sorted(updates,key=lambda x:x.get('update_id',0)):
        uid=upd.get('update_id'); msg=upd.get('message') or {}; chat=str((msg.get('chat') or {}).get('id','')); txt=msg.get('text')
        if not isinstance(uid,int) or not isinstance(txt,str): continue
        chosen=selection(txt)
        if chosen is None: continue
        if chat!=allowed:
            print(f'DIAG: MotoGP-Kommando Update {uid} stammt aus anderem Chat; ignoriert.')
            continue
        if already(uid):
            print(f'DIAG: Update {uid} wurde bereits verarbeitet.')
            continue
        print(f'DIAG: Verarbeite Update {uid}: {txt!r} -> {chosen}')
        if chosen:
            publish(posts,chosen,uid)
            send_message(f'✅ MotoGP: {len(chosen)} Content-Paket(e) freigegeben. Instagram und Facebook übernehmen jetzt über die bestehende Publisher-Kette.')
        else:
            send_message('❌ MotoGP-Tagesauswahl verworfen. Es wird nichts veröffentlicht.')
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(f'Update-ID: {uid}\nAntwort: {txt}\n',encoding='utf-8')
        # Kein zweiter getUpdates-Aufruf mehr: Telegram-Updates bleiben über Update-ID idempotent.
        handled=True
    if not handled:
        print('DIAG: Kein neues gültiges MotoGP-Freigabekommando gefunden.')

if __name__=='__main__': main()
