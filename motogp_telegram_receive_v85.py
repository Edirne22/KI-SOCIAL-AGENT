"""V8.5 human approval gate for Racing. QA PASS is never equal to human approval."""
from pathlib import Path
import re,sys,time
from telegram_bot import get_chat_id, get_updates, send_message, send_photo
import racing_run_controller as rc
from generate_agnes_media import agnes_generate_image, save_bytes
from pending_instagram import add_pending
SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md');STATE=Path('memory/MOTOGP_APPROVAL_STATE.md');PUBLISHED=Path('content/PUBLISHED.md')
MIN_SESSION_VERSION=18;MAX_SESSION_AGE_SECONDS=24*3600
RAW_BAD=('-->','by motogp.com','motogp-update:','eines der relevanten motogp-themen','die fakten stammen aus der offiziellen meldung')
def _active_batch():
    try:return rc._load().get('active_batch_id','')
    except Exception:return ''
def parse_session():
    if not SESSION.exists():
        return {}, {}
    raw = SESSION.read_text(encoding='utf-8')
    vm = re.search(r'(?m)^Session-Version:\s*(\d+)\s*$', raw)
    version = int(vm.group(1)) if vm else 0
    if version < MIN_SESSION_VERSION:
        return {}, {}
    if not re.search(r'(?m)^Approval-Status:\s*READY\s*$', raw) or not re.search(r'(?m)^QM:\s*PASS\s*$', raw):
        return {}, {}
    tm = re.search(r'(?m)^Session-Timestamp:\s*(\d+)\s*$', raw)
    if not tm:
        return {}, {}
    try:
        age = int(time.time()) - int(tm.group(1))
    except Exception:
        return {}, {}
    if age < -300 or age > MAX_SESSION_AGE_SECONDS:
        return {}, {}
    posts = {}
    problems = {}
    for m in re.finditer(r'(?ms)^## Beitrag\s+([1-5])\s*$\n(.*?)(?=^## Beitrag\s+[1-5]\s*$|\Z)', raw):
        n = int(m.group(1))
        sec = m.group(2)
        def f(name):
            x = re.search(rf'(?m)^{re.escape(name)}:\s*(.*)$', sec)
            return x.group(1).strip() if x else ''
        tx = re.search(r'(?ms)^Text:\s*(.*?)(?=^\s*Rechte-Gate:)', sec)
        post = {'title': f('Titel'), 'source': f('Quelle'), 'image': f('Instagram-Bild'), 'text': tx.group(1).strip() if tx else ''}

        # (a) QM-Gates
        failed_gate = next((g for g in ('QM', 'Racing-QM', 'Semantic-Fakten-QM')
                            if not re.search(rf'(?m)^{re.escape(g)}:\s*PASS\s*$', sec)), None)
        if failed_gate:
            problems[n] = f"{failed_gate} != PASS"
            continue

        # (b) RAW_BAD
        low = post['text'].casefold()
        bad_hit = next((x for x in RAW_BAD if x in low), None)
        if bad_hit:
            problems[n] = f"RAW_BAD-Treffer: {bad_hit!r}"
            continue

        # (c) Quelle
        if not post['source'].startswith('http'):
            problems[n] = "Quelle fehlt oder ungültig"
            continue

        # (d) Bild
        if not post['image'] or post['image'].lower() == 'auto':
            problems[n] = "Bild-Referenz fehlt oder 'auto'"
            continue
        if not Path(post['image']).is_file():
            problems[n] = f"Bilddatei fehlt: {post['image']}"
            continue

        posts[n] = post

    return posts, problems
def selection(text):
    v = re.sub(r'\s+', ' ', text.strip().lower())
    v = re.sub(r'/\s*', '', v)
    if 'motogp' not in v:
        return None
    v_clean = re.sub(r'\bmotogp\b', '', v).strip()
    v = f"motogp {v_clean}"
    if v in ('motogp alle', 'motogp ✅'):
        return [1, 2, 3, 4, 5]
    if v in ('motogp nein', 'motogp ❌'):
        return []
    m = re.fullmatch(r'motogp\s+([1-5](?:[\s,]+[1-5])*)', v)
    if not m:
        return None
    return sorted({int(x) for x in re.findall(r'[1-5]', m.group(1))})
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

        prompt = f"Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: {p['text'][:180]}"
        img_path = p["image"]
        try:
            img_bytes = agnes_generate_image(prompt)
            if img_bytes:
                save_bytes(img_bytes, img_path)
                print(f"MOTOGP: Agnes-Bild generiert für Auswahl {n}: {img_path}")
        except Exception as e:
            print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        add_pending(
            batch_id=batch,
            auswahl=n,
            titel=p["title"],
            text=p["text"],
            bild_pfad=img_path,
            prompt_fuer_agnes=prompt,
        )

        common_ig = f'Status: BILD_GENERIERT\nFreigabe: Telegram Racing\nRacing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\nRacing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{p["text"]}\nQuelle: {p["source"]}\nMedienstatus: EIGENE_KI_EDITORIALGRAFIK\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        caption = (
            f"🖼️ Instagram-Bild bereit für: {p['title']}\n"
            f"Auswahl: {n} (Batch: {batch})\n\n"
            f"Antworte mit:\n"
            f"- bild ✅ – posten\n"
            f"- bild ❌ – neu generieren"
        )
        try:
            send_photo(img_path, caption=caption)
        except Exception as e:
            print(f"MOTOGP: send_photo fehlgeschlagen: {e}")

    if blocks:PUBLISHED.write_text(existing.rstrip()+'\n\n'+'\n'.join(blocks).rstrip()+'\n',encoding='utf-8')
    return len(blocks)
def handle_one(uid, chat, txt):
    if chat != str(get_chat_id()):
        print(f"MOTOGP: Update {uid} aus fremdem Chat; quittiert.")
        return True
    if already(uid):
        print(f"MOTOGP: Update {uid} bereits verarbeitet; quittiert.")
        return True
    chosen = selection(txt)
    if chosen is None:
        print(f"MOTOGP: Update {uid} Kommando nicht erkannt; Text={txt!r}")
        try:
            send_message(
                "🤖 MotoGP-Kommando nicht erkannt.\n"
                "Beispiele: motogp 2,4 · motogp 2, 4 · motogp ✅ · motogp ❌ · motogp alle"
            )
        except Exception as e:
            print(f"MOTOGP: Hilfe senden fehlgeschlagen: {e}")
        return True
    batch = _active_batch()
    run = rc.get_run(batch) if batch else {}
    posts, problems = parse_session()

    if chosen:
        if not posts:
            send_message(
                '⛔ Session ungültig oder keine gültigen Beiträge gefunden. '
                'Nichts veröffentlicht.'
            )
        elif run.get('status') not in ('READY_FOR_APPROVAL', 'FREIGEGEBEN'):
            send_message(
                '⛔ Batch ist nicht im Status READY_FOR_APPROVAL. '
                'Nichts veröffentlicht.'
            )
        else:
            valid_chosen = [n for n in chosen if n in posts]
            missing_chosen = [n for n in chosen if n not in posts]

            if not valid_chosen:
                lines = ['⛔ Keiner deiner gewählten Beiträge ist verfügbar.']
                for n in missing_chosen:
                    lines.append(f'• Beitrag {n}: {problems.get(n, "unbekannt")}')
                send_message('\n'.join(lines))
            else:
                rc.transition(
                    batch, 'APPROVED',
                    telegram_update_id=uid, selection=valid_chosen
                )
                count = publish(posts, valid_chosen, uid, batch)
                rc.transition(batch, 'PUBLISHED', platform_blocks=count)

                msg = (
                    f'✅ Racing {batch}: {len(valid_chosen)} '
                    f'Content-Paket(e) freigegeben. '
                    f'{count} Plattform-Blöcke wurden übergeben.'
                )
                if missing_chosen:
                    msg += f'\n\n⚠️ Übersprungen: {", ".join(map(str, missing_chosen))}'
                    for n in missing_chosen:
                        msg += f'\n• Beitrag {n}: {problems.get(n, "unbekannt")}'
                send_message(msg)
    else:
        if batch:
            rc.transition(batch, 'CLOSED', decision='rejected_by_human')
        send_message('❌ Tagesauswahl verworfen. Es wird nichts veröffentlicht.')

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        f'Update-ID: {uid}\nRacing-Batch-ID: {batch}\nAntwort: {txt}\n',
        encoding='utf-8'
    )
    return True
def main():
    if len(sys.argv) >= 4:
        # Unverarbeitete Updates werden quittiert, nicht als Fehler gewertet.
        handle_one(int(sys.argv[1]), sys.argv[2], sys.argv[3])
        return
    for upd in sorted(get_updates(),key=lambda x:x.get('update_id',0)):
        uid=upd.get('update_id');msg=upd.get('message') or {};txt=msg.get('text');chat=str((msg.get('chat') or {}).get('id',''))
        if isinstance(uid,int) and isinstance(txt,str) and selection(txt) is not None:handle_one(uid,chat,txt)
if __name__=='__main__':main()
