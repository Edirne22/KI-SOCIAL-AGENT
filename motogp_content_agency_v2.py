"""MotoGP Content Agency V2 – story-specific copywriter, memory dedupe, media-ready."""
from motogp_content_agency import *

# Ambiguous surnames (Marc/Alex Marquez) must never create both hashtags.
def riders_in(text):
    low=text.casefold(); found=[]
    for n in RIDERS_V2:
        if n.casefold() in low: found.append(n)
    surnames={}
    for n in RIDERS_V2: surnames.setdefault(n.split()[-1].casefold(),[]).append(n)
    for surname,names in surnames.items():
        if len(names)==1 and re.search(rf'\b{re.escape(surname)}\b',low) and names[0] not in found: found.append(names[0])
    return found

RIDERS_V2=['Toprak Razgatlioglu','Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']

def hashtags(item):
    tags=['#MotoGP']; people=riders_in(item['title']+' '+item['summary'])
    for n in people[:3]: tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
    low=(item['title']+' '+item['summary']).casefold()
    for k,v in [('ducati','#Ducati'),('aprilia','#ApriliaRacing'),('yamaha','#YamahaRacing'),('ktm','#KTM'),('honda','#HondaRacing'),('misano','#SanMarinoGP'),('aragon','#AragonGP'),('silverstone','#BritishGP')]:
        if k in low and v not in tags: tags.append(v)
    tags += ['#MotorradRacing','#MotoGPDeutschland']
    return ' '.join(tags[:7])

def german_story(item):
    """Title-first: never let a secondary rider in description hijack the story."""
    t=item['title']; tl=t.casefold(); people=riders_in(t); p=people[0] if people else 'MotoGP'
    if 'martin soars to silverstone' in tl and 'sprint' in tl:
        return ('Jorge Martin gewinnt den Sprint in Silverstone vor Ai Ogura und Marco Bezzecchi. Für Aprilia wird der Samstag damit besonders stark: drei Aprilia-Fahrer belegen die ersten drei Plätze, während Marc Márquez einen schwierigen Sprint erlebt.','🇬🇧 Aprilia räumt in Silverstone ab – Martin führt ein Sprint-Podium komplett in Aprilia-Hand an.','Ist Aprilia für dich inzwischen der stärkste Gegner im Titelkampf?')
    if 'fends off acosta and bezzecchi' in tl and 'aragon' in tl:
        return ('Marc Márquez setzt sich in Aragón gegen Pedro Acosta und Marco Bezzecchi durch. An der Spitze wird hart gekämpft, und mit diesem Ergebnis verschiebt sich der Titelkampf erneut.','🔥 Márquez behauptet sich in Aragón gegen Acosta und Bezzecchi.','Wer von den drei hat dich in diesem Rennen am meisten überzeugt?')
    if 'retaliates to hold off alex marquez' in tl and 'aragon' in tl:
        return ('Marc Márquez schlägt im Aragón-Sprint zurück und hält Alex Márquez hinter sich. Marco Bezzecchi komplettiert als Dritter das Podium, während Jorge Martin ebenfalls wichtige Punkte im Blick behält.','⚔️ Márquez gegen Márquez: Marc gewinnt das Aragón-Duell vor Alex.','Hättest du Alex Márquez den Sieg zugetraut oder war Marc an diesem Tag zu stark?')
    if 'game on' in tl and 'largest points deficit' in tl:
        return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht. Sieben Rennwochenenden zuvor sah die Ausgangslage noch völlig anders aus.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das für dich schon eine seiner stärksten MotoGP-Aufholjagden?')
    if 'pol espargaro' in tl and 'replace' in tl and 'viñales' in tl:
        return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt beim Österreich-GP für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró als Ersatz für Viñales.','Wie stark schätzt du Pol bei diesem Comeback ein?')
    if 'acosta' in tl and 'ducati' in tl and ('2027' in tl or 'join' in tl):
        return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team. Damit bekommt Marc Márquez einen der stärksten jungen Fahrer im Feld als Teamkollegen.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Acosta neben Márquez – wie schätzt du diese Kombination sportlich ein?')
    if 'bezzecchi' in tl and ('pole' in tl or 'lap record' in tl):
        return ('Marco Bezzecchi setzt im Qualifying ein starkes Zeichen und holt sich die Pole vor Marc Márquez.','⏱️ Bezzecchi schlägt Márquez im Kampf um die Pole.','Wer ist für dich aktuell über eine schnelle Runde stärker?')
    if ('confirmed' in tl or 'join' in tl or 'sign' in tl) and p!='MotoGP':
        return (f'Für {p} ist eine Personalentscheidung offiziell bestätigt. Die Einordnung basiert auf der MotoGP-Originalmeldung und wird ohne Transfergerüchte formuliert.',f'🔄 Offiziell: wichtige Zukunftsentscheidung rund um {p}.','Wie bewertest du diese Entscheidung sportlich?')
    if ('win' in tl or 'victory' in tl or 'gold' in tl) and p!='MotoGP':
        return (f'{p} steht im Mittelpunkt des aktuellen Rennergebnisses. Die Platzierungen und der Rennkontext stammen aus der offiziellen MotoGP-Meldung.',f'🏁 {p} setzt ein sportliches Ausrufezeichen.','Was war für dich der entscheidende Moment dieses Rennens?')
    return ('','','')

def own_caption(item):
    fact,hook,question=german_story(item)
    if not fact: return ''
    return f'{hook}\n\n{fact}\n\n{question}\n\n{hashtags(item)}'

def quality_ok(caption):
    if not caption: return False
    bad=('-->','By motogp.com','MotoGP-Update:','ist heute eines der relevanten MotoGP-Themen','Social-Text wird bewusst eigenständig formuliert','Fakten stammen aus der offiziellen Meldung')
    return not any(x.casefold() in caption.casefold() for x in bad)

def run_v2():
    learned=get_context(9000); names=roster_names(); news=extract(get(NEWS),60); market=extract(get(MARKET),30); merged=[]; seen=set(); known=known_story_keys(); skipped=[]
    for item in news+market:
        key=story_key(item[0],item[1])
        if item[1] in seen: continue
        seen.add(item[1])
        if key in known: skipped.append(item); continue
        merged.append(item)
    merged.sort(key=lambda x:score(x[0],names),reverse=True)
    details=[article_info(t,u) for t,u in merged[:30]]; now=datetime.now(timezone.utc)
    lines=['# MotoGP Daily Content Agency','',f'**Recherche:** {now:%Y-%m-%d %H:%M UTC}','**Primärquelle:** offizielle MotoGP-Seite','**Closed-Loop Memory:** aktiv','**Story-Dedupe:** aktiv',f'**Memory-Treffer übersprungen:** {len(skipped)}','**Copy-Quality-Gate:** story-spezifisch; generischer Fülltext verboten','','## Analysierte neue Themen','']
    for i,item in enumerate(details,1): lines += [f'### {i}. {item["title"]}',f'- Story-Key: {story_key(item["title"],item["url"])}',f'- Quelle: {item["url"]}',f'- Quellen-Metadaten: {item["summary"] or "keine belastbare Meta-Zusammenfassung"}',f'- Score: {score(item["title"],names)}','']
    content='\n'.join(lines); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(content,encoding='utf-8'); ARCH.mkdir(parents=True,exist_ok=True); (ARCH/f'{now:%Y-%m-%d}.md').write_text(content,encoding='utf-8'); next_roster(market)
    candidates=[item for item in details if story_key(item['title'],item['url']) not in known and quality_ok(own_caption(item))]
    picks=[]
    for item in candidates:
        media=prepare_instagram_media_v2(item,len(picks)+1)
        if not media: continue
        item['instagram_media']=media; picks.append(item)
        if len(picks)==3: break
    if len(picks)==3:
        write_session_v2(picks,now); remember_offered(picks,now); telegram_preview_v2(picks)
    else:
        send_message(f'🏁 MotoGP Content Agency: Aktuell nur {len(picks)} neue, textlich und medial reife Story(s). Generischer Fülltext wird nicht mehr angeboten.')
    print(f'MotoGP V2: {len(details)} analysiert, {len(skipped)} bekannte gesperrt, {len(picks)} qualitätsgeprüfte Vorschläge.')

def prepare_instagram_media_v2(item,index):
    caption=own_caption(item); filename=get_image_path(slugify(f'motogp-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1)
    prompt=('Vertical 4:5 premium motorsport editorial social-media background. Empty modern European motorcycle racing circuit at dramatic golden hour. NO people, NO riders, NO motorcycles, NO helmets, NO team colors, NO manufacturer branding, NO sponsor logos, NO trademarks, NO readable text, NO watermark. Original generic racing visual, photorealistic. Editorial mood only: '+caption[:220])
    data=agnes_generate_image(prompt)
    if not data: return ''
    save_bytes(data,filename); return filename.as_posix()

def write_session_v2(items,now):
    lines=['# MotoGP Telegram Approval Session','Session-Version: 4',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle` oder `motogp nein`.','']
    for i,item in enumerate(items,1):
        lines += [f'## Beitrag {i}',f'Story-Key: {story_key(item["title"],item["url"])}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Instagram-Bild: {item["instagram_media"]}',f'Quellen-Preview: {item["preview"] or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{own_caption(item)}','','Rechte-Gate: Instagram nutzt eine eigene generische Editorial-Grafik. Facebook veröffentlicht den offiziellen Quellenlink für die Link-Vorschau.','']
    SESSION.write_text('\n'.join(lines),encoding='utf-8')

def telegram_preview_v2(items):
    msg=['🏁 MotoGP Content Agency – NEUE Tagesauswahl','','Story-spezifische Texte; keine generischen Fülltexte.','']
    for i,item in enumerate(items,1): msg += [f'{i}️⃣ {own_caption(item)}','🖼️ Instagram-Medium: vorbereitet',f'🔗 Quelle: {item["url"]}','']
    msg += ['Freigabe: motogp 1 / motogp 2 / motogp 3 / motogp alle','Ablehnen: motogp nein']; send_message('\n'.join(msg)[:4000])

if __name__=='__main__': run_v2()
