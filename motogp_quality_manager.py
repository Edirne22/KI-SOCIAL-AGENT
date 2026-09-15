"""Finales Domain-QM für Racing-Pakete vor Chief-QM und Telegram – V8.4."""
import re
BANNED=('motogp im fokus','eines der relevanten motogp-themen','die fakten stammen aus der offiziellen meldung','der social-text wird bewusst eigenständig formuliert','für die einordnung verwenden wir ausschließlich','was ist für dich der spannendste punkt an dieser story')
ENGLISH_MARKERS=(' out the ',' quickest ',' reigning ',' leads ',' opening stint ',' beats ',' pole in ',' qualifying ',' line-up ',' revealed ',' denies ',' points cover ',' world champion ',' sprint stand-off ',' from 2027 ',' alongside ',' weekend at ',' does the business ')
TURKISH=('toprak razgatlioglu','can oncu','deniz oncu','bahattin sofuoglu','zayn sofuoglu')
RIDERS={'marcmarquez':'marc marquez','alexmarquez':'alex marquez','pedroacosta':'pedro acosta','jorgemartin':'jorge martin','marcobezzecchi':'marco bezzecchi','fabioquartararo':'fabio quartararo','francescobagnaia':'francesco bagnaia','toprakrazgatlioglu':'toprak razgatlioglu','canoncu':'can oncu','denizoncu':'deniz oncu','bahattinsofuoglu':'bahattin sofuoglu','zaynsofuoglu':'zayn sofuoglu'}
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def review(item,caption):
 errors=[];low=fold(caption);source=fold((item.get('title') or '')+' '+(item.get('summary') or ''))
 for p in BANNED:
  if fold(p) in low:errors.append('verbotener/generischer Stil: '+p)
 # Hartes Sprach-Gate: englische News-Blöcke dürfen nie als deutscher Post durchgehen.
 padded=' '+low+' '
 hits=[m for m in ENGLISH_MARKERS if m in padded]
 if len(hits)>=2:errors.append('Deutsch-Gate FAIL: englischer Nachrichtenblock erkannt')
 # Türkische Flagge ausschließlich bei den fünf definierten Turkish Riders.
 if '🇹🇷' in caption and not any(fold(n) in low for n in TURKISH):errors.append('Turkish-Flag ohne Turkish Rider')
 parts=[p.strip() for p in caption.split('\n\n') if p.strip()]
 if len(parts)<4:errors.append('Poststruktur unvollständig')
 if '?' not in caption:errors.append('keine Community-Frage')
 tags=re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption)
 if not (4<=len(tags)<=7):errors.append('Hashtag-Anzahl nicht 4–7')
 source_riders=[name for name in RIDERS.values() if fold(name) in source];caption_riders=[name for name in RIDERS.values() if fold(name) in low]
 nums=set(re.findall(r'\b\d{1,4}\b',source)) & set(re.findall(r'\b\d{1,4}\b',low))
 if source_riders and not set(source_riders)&set(caption_riders):errors.append('Text nicht an den Fahrer der Quelle gebunden')
 if not source_riders and not nums:
  title_words=[w for w in re.findall(r'[a-z0-9]+',fold(item.get('title',''))) if len(w)>=5 and w not in {'motogp','worldsbk','worldssp','confirmed','title','sprint'}]
  if title_words and not any(w in low for w in title_words[:8]):errors.append('Text nicht konkret genug an Artikel gebunden')
 compact={fold(t[1:]) for t in tags}
 for tag,name in RIDERS.items():
  if tag in compact and fold(name) not in source:errors.append('unpassender Fahrer-Hashtag: #'+tag)
 if re.search(r'\b(quelle|redaktion|social-text|offizielle meldung)\b',low):errors.append('interne Quellen-/Redaktionssprache im Post')
 return not errors,errors
def review_batch(items):
 seen=set();result=[]
 for item in items:
  caption=item.get('caption','').strip();fp=re.sub(r'#[^\s]+','',fold(caption));fp=re.sub(r'\s+',' ',fp).strip();ok,errors=review(item,caption)
  if fp in seen:ok=False;errors.append('Copy-Duplikat innerhalb derselben Auswahl')
  seen.add(fp);result.append((ok,errors))
 return result
