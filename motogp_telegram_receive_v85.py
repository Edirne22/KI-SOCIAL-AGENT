"""V8.5 human approval gate for Racing. QA PASS is never equal to human approval."""
from pathlib import Path
import re,sys,time,json
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from telegram_bot import get_chat_id, get_updates, send_message, send_photo
import racing_run_controller as rc
from generate_agnes_media import agnes_generate_image, save_bytes
from instagram_publish import download_og_image_for_instagram, generate_buelent_caption
from pending_instagram import add_pending
from asset_paths import get_image_path
SESSION=Path('memory/MOTOGP_APPROVAL_SESSION.md');TURKISH_SESSION=Path('memory/TURKISH_RIDER_APPROVAL.json');TURKISH_PREVIEWS=Path('memory/TURKISH_RIDER_HUMAN_PREVIEWS.json');STATE=Path('memory/MOTOGP_APPROVAL_STATE.md');PUBLISHED=Path('content/PUBLISHED.md')
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
    """Parse MotoGP approvals 1-5, including inclusive ranges."""
    v=re.sub(r'\s+',' ',str(text or '').strip().lower())
    v=re.sub(r'^/\s*','',v)
    m=re.fullmatch(r'motogp\s+(.+)',v)
    if not m:return None
    choice=m.group(1).strip()
    if choice in ('alle','✅'):return [1,2,3,4,5]
    if choice in ('nein','❌'):return []
    choice=re.sub(r'\s*[-–—]\s*','-',choice)
    choice=re.sub(r'\s*,\s*',',',choice)
    if not re.fullmatch(r'[1-5](?:-[1-5])?(?:,[1-5](?:-[1-5])?)*',choice):return None
    out=set()
    for part in choice.split(','):
        if '-' in part:
            x,y=(int(n) for n in part.split('-',1))
            if x>y:return None
            out.update(range(x,y+1))
        else:out.add(int(part))
    return sorted(out)



def turkish_publish_interval(text):
    v=re.sub(r'\s+',' ',str(text or '').strip().casefold())
    m=re.search(r'(?:alle|abstand(?:\s+von)?|im\s+abstand(?:\s+von)?)\s+(\d+)\s*(minute|minuten|stunde|stunden)',v)
    if m:return int(m.group(1))*(60 if m.group(2).startswith('stunde') else 1)
    if re.search(r'\b(jede\s+stunde|stündlich|stuendlich)\b',v):return 60
    return None

def turkish_t_order(text):
    out=[]
    for raw in re.findall(r'(?i)\bt\s*([1-9]|1\d|20)\b',str(text or '')):
        n=int(raw)
        if n not in out:out.append(n)
    return out

def turkish_actions(text):
    """Parse mixed human actions by nearest action phrase."""
    v=re.sub(r'\s+',' ',str(text or '').strip().casefold())
    v=re.sub(r'nicht\s+(?:posten|veröffentlichen|veroeffentlichen)', ' nichtposten ', v)
    action_pat=r'nichtposten|verwerfen|löschen|loeschen|ändern|aendern|überarbeiten|ueberarbeiten|umschreiben|bearbeiten|post(?:en|e|et)?|veröffentlichen|veroeffentlichen|freigeben'
    def kind(word):
        if word.casefold()=='nichtposten' or re.fullmatch(r'verwerfen|löschen|loeschen',word):return 'drop'
        if re.fullmatch(r'ändern|aendern|überarbeiten|ueberarbeiten|umschreiben|bearbeiten',word):return 'edit'
        return 'post'
    hits=list(re.finditer(r'(?i)\b(?:'+action_pat+r')\b',v))
    if not hits:return None
    tnums=[(m.start(),int(m.group(1))) for m in re.finditer(r'(?i)\bt\s*([1-9]|1\d|20)\b',v)]
    if not tnums:return None
    assigned={};cursor=0
    for h in hits:
        action=kind(h.group(0))
        for pos,n in tnums:
            if cursor<=pos<h.start():
                if n in assigned and assigned[n]!=action:return None
                assigned[n]=action
        cursor=h.end()
    last_action=kind(hits[-1].group(0))
    for pos,n in tnums:
        if pos>=cursor:
            if n in assigned and assigned[n]!=last_action:return None
            assigned[n]=last_action
    out=[]
    for action in ('post','edit','drop'):
        nums=sorted(n for n,a in assigned.items() if a==action)
        if nums:out.append((action,nums))
    return out

def turkish_action(text):
    actions=turkish_actions(text)
    return actions[0] if actions and len(actions)==1 else None

def turkish_selection(text):
    """Parse Turkish-Rider approvals T1-T20, including inclusive ranges.

    Examples: T1, T2, T1,T4, T1-4, T 1-4, turkish 1-4, turkish 12.
    turkish alle deliberately means the visible T1-T5 only.
    """
    v=re.sub(r'\s+',' ',str(text or '').strip().lower())
    v=re.sub(r'^/\s*','',v)
    if v in ('turkish liste','t liste'):
        return None
    if v in ('turkish alle','t alle','turkish ✅','t ✅'):
        return [1,2,3,4,5]
    if v in ('turkish nein','t nein','turkish ❌','t ❌'):
        return []

    m=re.fullmatch(r'(?:turkish|t)\s*(.+)',v)
    if not m:return None
    choice=m.group(1).strip()
    choice=re.sub(r'(?i)\bt\s*(?=\d)','',choice)
    choice=re.sub(r'\s*[-–—]\s*','-',choice)
    choice=re.sub(r'\s*,\s*',',',choice)
    if not re.fullmatch(r'\d{1,2}(?:-\d{1,2})?(?:,\d{1,2}(?:-\d{1,2})?)*',choice):
        return None
    out=set()
    for part in choice.split(','):
        if '-' in part:
            a,b=(int(x) for x in part.split('-',1))
            if not (1<=a<=20 and 1<=b<=20) or a>b:return None
            out.update(range(a,b+1))
        else:
            n=int(part)
            if not 1<=n<=20:return None
            out.add(n)
    return sorted(out)

def turkish_list_requested(text):
    v=re.sub(r'\s+',' ',str(text or '').strip().lower())
    v=re.sub(r'^/\s*','',v)
    return v in ('turkish liste','t liste')

def handle_turkish_list(uid,chat):
    if chat!=str(get_chat_id()):return True
    if already(uid):return True
    rows=parse_turkish_session()
    if not rows:
        send_message('⛔ Keine aktuelle Turkish-Rider-Historie verfügbar.')
        return True
    lines=['🇹🇷 TURKISH RIDER – TOP-20 HISTORIE','Auswahl danach z. B.: turkish 12 oder T12,T17','']
    for n in sorted(rows):
        x=rows[n]
        lines.append(f'T{n} | {x.get("turkish_rider") or "Turkish Rider"} | {x.get("title","")}\n🔗 {x.get("url","")}')
    chunks=[];cur=''
    for entry in lines:
        add=entry+'\n'
        if cur and len(cur)+len(add)>3900:
            chunks.append(cur.rstrip());cur=''
        cur+=add
    if cur:chunks.append(cur.rstrip())
    for chunk in chunks:send_message(chunk)
    return True

def parse_turkish_session():
    try:data=json.loads(TURKISH_SESSION.read_text(encoding='utf-8'))
    except Exception:return {}
    if int(time.time())-int(data.get('created_at',0))>24*3600:return {}
    return {int(x['n']):x for x in data.get('items',[]) if isinstance(x,dict) and str(x.get('n','')).isdigit()}


def _load_turkish_previews():
    try:
        data=json.loads(TURKISH_PREVIEWS.read_text(encoding='utf-8'))
        if int(time.time())-int(data.get('created_at',0))>24*3600:return {}
        return {int(k):v for k,v in data.get('items',{}).items()}
    except Exception:return {}

def handle_turkish_action(uid,chat,txt):
    cmds=turkish_actions(txt)
    if not cmds:return False
    if len(cmds)>1:
        ok=True
        for action,chosen in cmds:
            synthetic=' '.join('T'+str(n) for n in chosen)+' '+({'post':'posten','edit':'überarbeiten','drop':'nicht posten'}[action])
            ok=handle_turkish_action(uid,chat,synthetic) and ok
        return ok
    action,chosen=cmds[0]
    order=[n for n in turkish_t_order(txt) if n in chosen]
    chosen=order or chosen
    rows=_load_turkish_previews()
    selected=[n for n in chosen if n in rows]
    if not selected:
        send_message('⛔ Keine passende aktuelle Turkish-Rider-Vorschau gefunden.')
        return True
    if action=='post':
        posts={}
        for n in selected:
            p=rows[n]
            posts[n]={'title':p.get('title',''),'source':p.get('source',''),'image':get_image_path(f'turkish-human-{n}-{p.get("rider","")}').as_posix(),'text':p.get('text',''),'caption_final':True,'human_final':True}
        batch=(_active_batch() or f'turkish-{int(time.time())}')+'-TR-HUMAN'
        count=publish(posts,selected,uid,batch)
        plan=' → '.join('T'+str(n) for n in selected)
        send_message(f'✅ Deine Freigabe-Reihenfolge: {plan} · exakt die gezeigten Texte · je Publisher-Rundlauf der nächste Beitrag · {count} Plattform-Blöcke vorbereitet.')
        return True
    if action=='drop':
        for n in selected: rows.pop(n,None)
        TURKISH_PREVIEWS.write_text(json.dumps({'created_at':int(time.time()),'items':{str(k):v for k,v in rows.items()}},ensure_ascii=False,indent=2),encoding='utf-8')
        send_message(f'❌ Nicht posten: {", ".join("T"+str(n) for n in selected)}.')
        return True
    import motogp_content_agency_v2 as agency
    import turkish_editor_qm as turkish_lane
    for n in selected:
        source=dict(parse_turkish_session().get(n) or {})
        if not source:continue
        result=turkish_lane.human_preview(source,n,agency);x=result.get('item') or source
        rows[n].update(text=x.get('caption',rows[n].get('text','')))
        body=f'T{n} · ÜBERARBEITET · {x.get("turkish_rider","Turkish Rider")}\\n\\n{rows[n]["text"]}\\n\\nDanach: posten / überarbeiten / nicht posten'
        preview=rows[n].get('preview','')
        if not (preview and agency._send_turkish_source_photo(preview,body)):send_message(body)
    TURKISH_PREVIEWS.write_text(json.dumps({'created_at':int(time.time()),'items':{str(k):v for k,v in rows.items()}},ensure_ascii=False,indent=2),encoding='utf-8')
    return True

def handle_turkish(uid,chat,txt):
    if chat!=str(get_chat_id()):return True
    if already(uid):return True
    chosen=turkish_selection(txt)
    if chosen is None:return False
    if not chosen:
        send_message('❌ Turkish-Rider-Auswahl verworfen. Es wird nichts veröffentlicht.')
    else:
        rows=parse_turkish_session()
        selected=[n for n in chosen if n in rows]
        if not selected:
            send_message('⛔ Keiner der gewählten Turkish-Rider-Vorschläge ist in der aktuellen Session verfügbar.')
        else:
            import motogp_content_agency_v2 as agency
            from racing_v855_hardening import install as install_v855_hardening
            import turkish_editor_qm as turkish_lane
            install_v855_hardening(agency)
            previews=[];technical=[]
            for n in selected:
                x=dict(rows[n])
                result=turkish_lane.human_preview(x,n,agency)
                x=result.get("item") or x
                if result.get("status")=="HUMAN_PREVIEW":
                    previews.append((n,x,list(result.get("reasons") or [])))
                else:
                    technical.append((n,list(result.get("reasons") or [])))
            send_message(f'🇹🇷 Manuelle Turkish-Auswahl: {len(previews)} VORSCHAU, {len(technical)} TECHNISCHER FEHLER.\nDu entscheidest. Kein QM kann diese Vorschau blockieren; automatische Veröffentlichung bleibt aus.')
            for n,x,warnings in previews:
                preview=x.get("preview","")
                warn=("\n\n⚠️ Hinweise: "+"; ".join(warnings[:6])) if warnings else ""
                body=f'T{n} · {x.get("turkish_rider","Turkish Rider")}\n\n{x.get("caption","(kein Text)")}{warn}\n\nDanach: posten / ändern / nicht posten'
                if preview and agency._send_turkish_source_photo(preview,body):
                    continue
                send_message(body+"\n\n🖼️ Quell-Vorschaubild nicht abrufbar.")
            saved={"created_at":int(time.time()),"items":{}}
            for n,x,_ in previews:
                saved["items"][str(n)]={"n":n,"title":x.get("title",""),"source":x.get("url",""),"preview":x.get("preview",""),"rider":x.get("turkish_rider",""),"text":x.get("caption","")}
            TURKISH_PREVIEWS.parent.mkdir(parents=True,exist_ok=True)
            TURKISH_PREVIEWS.write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding="utf-8")
            for n,reasons in technical:
                send_message(f'🛠️ T{n} technisch nicht fertig: {"; ".join(reasons[:4])}')
    STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(f'Update-ID: {uid}\nAntwort: {txt}\n',encoding='utf-8')
    return True

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
def _schedule_lines(schedule):
    return f'Geplant-fuer: {schedule}\n' if schedule else ''

def _migrate_legacy_turkish_instagram(existing,p,n,uid,batch,img_path,media_status):
    if not p.get('human_final'):return existing,False
    pattern=re.compile(r'(^## Instagram\\s*\\n.*?)(?=^## |\\Z)',re.MULTILINE|re.DOTALL)
    wanted=_normalize_text(p.get('text',''))
    for m in pattern.finditer(existing):
        block=m.group(1)
        if '-TR-HUMAN' not in block or not re.search(r'(?mi)^Status:\\s*BILD_GENERIERT\\s*
    schedules=schedules or {}
    PUBLISHED.parent.mkdir(parents=True,exist_ok=True);existing=PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n';blocks=[]
    existing_texts=get_existing_published_texts()
    for n in chosen:
        p=posts.get(n)
        if not p:continue
        marker=f'Racing-Batch-ID: {batch}\nMotoGP-Auswahl: {n}'
        if marker in existing:continue
        norm_post_text=_normalize_text(p["text"])
        is_existing_duplicate=bool(norm_post_text and norm_post_text in existing_texts)

        prompt = f"Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: {p['text'][:180]}"
        img_path = p["image"]
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        existing,migrated=_migrate_legacy_turkish_instagram(existing,p,n,uid,batch,img_path,media_status)
        if migrated:
            print(f"TURKISH HUMAN MIGRATION: bestehender Instagram-Block T{n} -> FREIGEGEBEN ({img_path})")
            continue
        if is_existing_duplicate:
            print(f"DUPLIKAT ERKANNT: {p['title']} bereits vorhanden, übersprungen")
            continue
        if norm_post_text:existing_texts.add(norm_post_text)

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    elif existing != (PUBLISHED.read_text(encoding='utf-8') if PUBLISHED.exists() else '# Freigegebene Beiträge\n'):
        PUBLISHED.write_text(existing,encoding='utf-8')
    return len(blocks)
def handle_one(uid, chat, txt):
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
,block):continue
        tm=re.search(r'(?ms)^Text:\\s*(.*?)(?=^(?:Quelle|Medienstatus|Bild):|\\Z)',block)
        if not tm or _normalize_text(tm.group(1))!=wanted:continue
        updated=re.sub(r'(?mi)^Status:\\s*BILD_GENERIERT\\s*
    schedules=schedules or {}
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
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
,'Status: FREIGEGEBEN',block,count=1)
        updated=re.sub(r'(?mi)^Bild:\\s*\\S+\\s*
    schedules=schedules or {}
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
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
,f'Bild: {img_path}',updated,count=1)
        updated=re.sub(r'(?mi)^Medienstatus:\\s*.*
    schedules=schedules or {}
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
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
,f'Medienstatus: {media_status}',updated,count=1)
        updated=re.sub(r'(?mi)^Telegram-Update-ID:\\s*.*
    schedules=schedules or {}
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
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
,f'Telegram-Update-ID: {uid}',updated,count=1)
        return existing[:m.start()]+updated+existing[m.end():],True
    return existing,False

def publish(posts,chosen,uid,batch,schedules=None):
    schedules=schedules or {}
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
        media_status = "QUELLE_BESTÄTIGT"
        og_path = download_og_image_for_instagram(p["source"], img_path)
        if og_path:
            img_path = og_path
            print(f"MOTOGP: og:image der Quelle verwendet für Auswahl {n}: {img_path}")
        else:
            media_status = "EIGENE_KI_EDITORIALGRAFIK"
            try:
                img_bytes = agnes_generate_image(prompt)
                if img_bytes:
                    save_bytes(img_bytes, img_path)
                    print(f"MOTOGP: Kein og:image – Agnes-Fallback für Auswahl {n}: {img_path}")
            except Exception as e:
                print(f"MOTOGP: Agnes Bild-Generierung übersprungen / fehlgeschlagen: {e}")

        instagram_text = p["text"] if p.get("caption_final") else generate_buelent_caption(p["text"])

        if not p.get('human_final'):
            add_pending(
                batch_id=batch,
                auswahl=n,
                titel=p["title"],
                text=instagram_text,
                bild_pfad=img_path,
                prompt_fuer_agnes=prompt,
            )

        scheduled=_schedule_lines(schedules.get(n))
        ig_status = 'FREIGEGEBEN' if p.get('human_final') else 'BILD_GENERIERT'
        common_ig = f'Status: {ig_status}\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'
        common_fb = f'Status: FREIGEGEBEN\nFreigabe: Telegram Racing\n{scheduled}Racing-Batch-ID: {batch}\nTelegram-Update-ID: {uid}\nMotoGP-Auswahl: {n}\nTitel: {p["title"]}\n'

        blocks += [
            f'## Instagram\n{common_ig}Text:\n{instagram_text}\nQuelle: {p["source"]}\nMedienstatus: {media_status}\nBild: {img_path}\n',
            f'## Facebook\n{common_fb}Text:\n{p["text"]}\n\n{p["source"]}\nQuelle: {p["source"]}\nLink-Preview: offiziell\n'
        ]

        if not p.get('human_final'):
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
    if turkish_actions(txt) is not None:
        return handle_turkish_action(uid,chat,txt)
    if turkish_list_requested(txt):
        return handle_turkish_list(uid,chat)
    if turkish_selection(txt) is not None:
        return handle_turkish(uid,chat,txt)
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
        if isinstance(uid,int) and isinstance(txt,str) and (selection(txt) is not None or turkish_selection(txt) is not None or turkish_actions(txt) is not None or turkish_list_requested(txt)):handle_one(uid,chat,txt)
if __name__=='__main__':main()
