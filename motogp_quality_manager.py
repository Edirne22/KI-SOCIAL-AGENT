"""Finales Domain-QM für Racing-Pakete vor Semantic-/Chief-QM – V8.4.6.1."""
import re
from racing_language_rules import deterministic_errors as lexicon_errors
TURKISH=('toprak razgatlioglu','can oncu','deniz oncu','bahattin sofuoglu','zayn sofuoglu')
RIDER_NAMES=('Marc Marquez','Alex Marquez','Pedro Acosta','Jorge Martin','Marco Bezzecchi','Fabio Quartararo','Francesco Bagnaia','Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado','Iker Lecuona','Alvaro Bautista','Andrea Iannone','Sam Lowes','Alex Lowes','Jonathan Rea','Stefano Manzi','Jeremy Alcoba','Marcos Ramirez','Sergio Garcia','Alberto Surra')
RIDERS={re.sub(r'[^a-z0-9]','',n.casefold()):n for n in RIDER_NAMES}
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_matches(text):
 low=fold(text);out=[];full_hits=set()
 for n in RIDER_NAMES:
  f=fold(n)
  if re.search(r'(?<![a-z])'+re.escape(f)+r'(?![a-z])',low):out.append(n);full_hits.add(n)
 surname_map={}
 for n in RIDER_NAMES:surname_map.setdefault(fold(n).split()[-1],[]).append(n)
 for last,owners in surname_map.items():
  if len(last)<5 or len(owners)!=1:continue
  if re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',low) and owners[0] not in full_hits:out.append(owners[0])
 return list(dict.fromkeys(out))
def rider_tag(rider):return '#'+re.sub(r'[^A-Za-z0-9]','',rider)
def repair_rider_hashtags(item,caption):
 source=(item.get('title') or '')+' '+(item.get('summary') or '');riders=rider_matches(source)[:2]
 if not riders:return caption
 tags=re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption);compact={fold(t[1:]) for t in tags};missing=[rider_tag(r) for r in riders if fold(re.sub(r'[^A-Za-z0-9]','',r)) not in compact]
 if not missing:return caption
 parts=caption.rsplit('\n\n',1)
 if len(parts)==2 and parts[1].lstrip().startswith('#'):
  existing=parts[1].split();room=max(0,7-len(existing));add=missing[:room]
  if len(add)<len(missing):
   protected=[t for t in existing if t.startswith(('#MotoGP','#WorldSBK','#WorldSSP')) or any(fold(t[1:])==fold(re.sub(r'[^A-Za-z0-9]','',r)) for r in riders)];generic=[t for t in existing if t not in protected];need=len(missing);existing=(protected+generic)[:max(0,7-need)];add=missing[:7-len(existing)]
  caption=parts[0]+'\n\n'+' '.join(dict.fromkeys(existing+add))
 else:caption=caption+'\n\n'+' '.join(missing[:2])
 item['caption']=caption;return caption
def review(item,caption):
 caption=repair_rider_hashtags(item,caption);errors=list(lexicon_errors(caption));low=fold(caption);source=fold((item.get('title') or '')+' '+(item.get('summary') or ''))
 if '🇹🇷' in caption and not any(fold(n) in low for n in TURKISH):errors.append('Turkish-Flag ohne Turkish Rider')
 parts=[p.strip() for p in caption.split('\n\n') if p.strip()]
 variant=item.get('structure_variant')
 if variant:
  body_parts=[p for p in parts if not p.lstrip().startswith('#')]
  min_parts={'HOOK_BODY_QUESTION':3,'BODY_QUESTION':2,'STORY_QUESTION':2,'FACT_FACT_FACT':4,'QUESTION_HOOK_BODY':2,'ZITAT_BODY':3}.get(variant)
  if min_parts is None:errors.append('unbekannte Poststruktur: '+str(variant))
  elif len(body_parts)<min_parts:errors.append('Poststruktur unvollständig')
  if variant!='FACT_FACT_FACT' and '?' not in caption:errors.append('keine Community-Frage')
 else:
  if len(parts)<4:errors.append('Poststruktur unvollständig')
  if '?' not in caption:errors.append('keine Community-Frage')
 tags=re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption)
 if not (4<=len(tags)<=7):errors.append('Hashtag-Anzahl nicht 4–7')
 source_riders=rider_matches(source)
 # The official WorldSBK headline for Bahattin currently shortens/misspells
 # Sofuoğlu as "Sofouglu". enrich_turkish() resolves that source context;
 # make the deterministic Racing-QM consume the resolved identity too.
 resolved_turkish=item.get('turkish_rider','')
 if resolved_turkish in RIDER_NAMES and resolved_turkish not in source_riders:source_riders.append(resolved_turkish)
 caption_riders=rider_matches(low)
 if source_riders and not set(source_riders)&set(caption_riders):errors.append('Text nicht an den Fahrer der Quelle gebunden')
 compact={fold(t[1:]) for t in tags}
 for rider in source_riders[:2]:
  expected=fold(re.sub(r'[^A-Za-z0-9]','',rider))
  if expected not in compact:errors.append('Fahrer-Hashtag fehlt: '+rider_tag(rider))
 for tag,name in RIDERS.items():
  if tag in compact and name not in source_riders:errors.append('unpassender Fahrer-Hashtag: #'+tag)
 nums=set(re.findall(r'\b\d{1,4}\b',source)) & set(re.findall(r'\b\d{1,4}\b',low))
 if not source_riders and not nums:
  title_words=[w for w in re.findall(r'[a-z0-9]+',fold(item.get('title',''))) if len(w)>=5 and w not in {'motogp','worldsbk','worldssp','confirmed','title','sprint'}]
  if title_words and not any(w in low for w in title_words[:8]):errors.append('Text nicht konkret genug an Artikel gebunden')
 if re.search(r'\b(quelle|redaktion|social-text|offizielle meldung)\b',low):errors.append('interne Quellen-/Redaktionssprache im Post')
 # V8.4.6.1: Zitatzeichen werden hier bewusst NICHT mehr final verworfen.
 # Der nachgeschaltete semantische Fakten-QM erkennt direkte/übersetzte Zitate,
 # liefert den konkreten Grund an den Redakteur zurück und erzwingt genau eine Neufassung.
 # Dadurch wird das Gate nicht gelockert: ohne Semantic-QM-PASS erreicht kein Text den Chief-QM.
 if errors:print('RACING-QM FAIL:',item.get('title','')[:90],'|','; '.join(errors))
 else:print('RACING-QM PASS:',item.get('title','')[:90])
 return not errors,errors
def review_batch(items):
 seen=set();result=[]
 for item in items:
  caption=item.get('caption','').strip();fp=re.sub(r'#[^\s]+','',fold(caption));fp=re.sub(r'\s+',' ',fp).strip();ok,errors=review(item,caption)
  if fp in seen:ok=False;errors.append('Copy-Duplikat innerhalb derselben Auswahl')
  seen.add(fp);result.append((ok,errors))
 return result
