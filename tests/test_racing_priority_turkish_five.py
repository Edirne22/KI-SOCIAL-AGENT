"""Regression: priority repair lane + independent Turkish-five preview."""
import motogp_content_agency_v2 as a
import turkish_riders_scout as trs
import motogp_telegram_receive_v85 as recv
import turkish_editor_qm as tqm
import inspect

def test_priority_marking_and_order():
 normal={'title':'Routine race report','summary':'race','url':'https://example.test/n','series':'MotoGP','source_series':'MotoGP','caption':'normal'}
 binder={'title':'Brad Binder joins BMW project','summary':'Brad Binder moves to BMW','url':'https://example.test/b','series':'WorldSBK','source_series':'WorldSBK','caption':'binder'}
 a.mark_priority(normal);a.mark_priority(binder)
 assert not normal.get('priority_repair')
 assert binder.get('priority_repair')
 ordered=a.ordered_pool([normal,binder],[])
 assert ordered[0] is binder

def test_top20_priority():
 x={'title':'Routine race report','summary':'race','url':'https://example.test/t','series':'MotoGP','source_series':'MotoGP','fallback_yesterday':True}
 a.mark_priority(x,'TOP20')
 assert x['priority_repair'] is True
 assert 'TOP20' in x['priority_reasons']


def test_central_turkish_rider_source_registry():
 from turkish_rider_names import RIDER_CONTEXT
 assert RIDER_CONTEXT['Toprak Razgatlıoğlu']['series']=='MotoGP'
 assert RIDER_CONTEXT['Deniz Öncü']['series']=='Moto2'
 assert RIDER_CONTEXT['Can Öncü']['series']=='WorldSSP'
 assert RIDER_CONTEXT['Bahattin Sofuoğlu']['series']=='WorldSSP'
 assert RIDER_CONTEXT['Zayn Sofuoğlu']['series']=='Karting'
 assert RIDER_CONTEXT['Zayn Sofuoğlu']['official_sources']==('https://www.iame-motorsport.com/iame-series-benelux',)
 assert all(v.get('official_sources') for v in RIDER_CONTEXT.values())
 assert len(RIDER_CONTEXT)>=12
 for rider in ('Oğuz Taşhan','İshak Demir Dönmez','Berkay Sarıay','Poyraz Bor','Orhan Karık','Alp Burak Albayrak','Efe Okur','Hasan Hüseyin Baş'):
  assert rider in RIDER_CONTEXT
  assert RIDER_CONTEXT[rider]['official_sources']
 assert trs.RIDER_SOURCES is RIDER_CONTEXT

def test_surname_only_turkish_riders_use_series_context():
 assert trs.rider_for('Oncu and Debise complete the second row','WorldSSP')=='Can Öncü'
 assert trs.rider_for('Oncu takes Moto2 front row','Moto2')=='Deniz Öncü'
 assert trs.rider_for('Razgatlioglu prepares for rookie campaign','MotoGP')=='Toprak Razgatlıoğlu'
 assert trs.rider_for('Sofuoglu in R3 BLU CRU title fight','WorldSBK')=='Zayn Sofuoğlu'
 assert trs.rider_for('Oncu update','')==''

def test_turkish_candidate_is_independent_and_deduplicated():
 raw=[];seen=set();meta={}
 url='https://example.test/current-oncu'
 assert a.add_turkish_candidate(raw,seen,meta,'Oncu current report',url,'Can Öncü')
 assert not a.add_turkish_candidate(raw,seen,meta,'Oncu duplicate',url,'Can Öncü')
 assert len(raw)==1 and meta[url]['turkish_rider']=='Can Öncü'
 # Regression: if Racing found the URL first, Turkish scout must still enrich metadata.
 raw2=[('Generic WorldSSP title',url)];seen2={url};meta2={url:{'source_series':'WorldSSP'}}
 assert not a.add_turkish_candidate(raw2,seen2,meta2,'Oncu current report',url,'Can Öncü')
 assert meta2[url]['turkish_rider']=='Can Öncü'

def test_turkish_preview_is_separate_and_limited():
 sent=[]
 old_send=a.send_message;old_photo=a.send_photo;old_og=a.extract_og_image_url;old_roster=a.roster_names
 try:
  a.send_message=lambda m:sent.append(m)
  photos=[]
  a.send_photo=lambda img,caption='':photos.append((img,caption))
  a.extract_og_image_url=lambda u:'https://img.example/test.jpg'
  a.roster_names=lambda:[]
  rows=[]
  for i in range(7):
   rows.append({'title':f'Toprak Razgatlioglu race news {i}','summary':'Toprak Razgatlioglu racing','url':f'https://example.test/tr{i}','published_at':'2026-09-26T10:00:00+00:00','series':'WorldSBK','source_series':'WorldSBK','turkish_rider':'Toprak Razgatlioglu'})
  from datetime import datetime,timezone
  out=a.turkish_five_preview(rows,datetime(2026,9,26,12,0,tzinfo=timezone.utc))
  assert len(out)==5
  assert len(photos)==5
  assert len(sent)==2
  assert 'NICHT automatisch freigegeben' in sent[0]
  assert 'T5' in photos[-1][1] and all('T6' not in p[1] for p in photos)
 finally:
  a.send_message=old_send;a.send_photo=old_photo;a.extract_og_image_url=old_og;a.roster_names=old_roster

def test_rider_centered_scout_uses_registered_official_sources():
 old_sources=trs.RIDER_SOURCES;old_anchors=trs._anchors
 try:
  trs.RIDER_SOURCES={'Can Öncü':{'series':'WorldSSP','official_sources':('https://official.test/can',)}}
  called=[]
  def fake_anchors(series,base,limit):
   called.append((series,base,limit))
   return [('Can Oncu race report','https://official.test/news/can','WorldSSP','Can Öncü')]
  trs._anchors=fake_anchors
  rows=trs.rider_centered_scout(120)
  assert called==[('WorldSSP','https://official.test/can',120)]
  assert rows==[('Can Oncu race report','https://official.test/news/can','Can Öncü','WorldSSP')]
 finally:
  trs.RIDER_SOURCES=old_sources;trs._anchors=old_anchors

def test_tmf_haberler_links_are_discovered_and_generic_titles_are_not_people():
 old_get=trs.requests.get;old_anchors=trs._anchors;old_remember=trs.remember_candidate
 try:
  class Response:
   text='<a href="/Haberler/Turk-Milli-Sporcu-Yarisi/">Turkish national motorcycle racer weekend report</a>'
   def raise_for_status(self): pass
  trs.requests.get=lambda *args,**kwargs:Response()
  rows=trs._anchors('TMF','https://www.tmf.org.tr/Haberler/',10)
  assert rows and rows[0][1]=='https://www.tmf.org.tr/Haberler/Turk-Milli-Sporcu-Yarisi/'
  trs._anchors=lambda *args:[('Turkish rider racing weekend report','https://www.tmf.org.tr/Haberler/generic/','TMF','')]
  remembered=[];trs.remember_candidate=lambda *args:remembered.append(args)
  assert trs.discovery_scout(10)==[]
  assert remembered==[]
 finally:
  trs.requests.get=old_get;trs._anchors=old_anchors;trs.remember_candidate=old_remember

def test_turkish_discovery_memory_does_not_auto_promote(tmp_path=None):
 import turkish_rider_memory as mem
 from pathlib import Path
 old_path=mem.MEMORY_PATH
 tmp_path=tmp_path or Path('/tmp/turkish-memory-regression')
 tmp_path.mkdir(parents=True,exist_ok=True)
 try:
  mem.MEMORY_PATH=tmp_path/'turkish.json'
  if mem.MEMORY_PATH.exists(): mem.MEMORY_PATH.unlink()
  row=mem.remember_candidate('New Turkish Rookie','Moto4','https://official.test/rookie','Turkish rookie result')
  assert row['status']=='candidate'
  data=mem.load()
  assert 'New Turkish Rookie' in data['discovery_candidates']
  assert 'New Turkish Rookie' not in data['riders']
  mem.remember_verified('New Turkish Rookie','Moto4',('https://official.test/rider',),'https://official.test/result')
  data=mem.load()
  assert data['riders']['New Turkish Rookie']['status']=='verified'
  assert 'New Turkish Rookie' not in data['discovery_candidates']
 finally:
  mem.MEMORY_PATH=old_path

def test_turkish_ten_day_window_and_selection_parser():
 sent=[];old_send=a.send_message;old_photo=a.send_photo;old_og=a.extract_og_image_url;old_roster=a.roster_names;old_sender=a._send_turkish_source_photo
 try:
  a.send_message=lambda m:sent.append(m);a.send_photo=lambda *args,**kwargs:None;a.extract_og_image_url=lambda u:'';a.roster_names=lambda:[];a._send_turkish_source_photo=lambda og,caption:False
  rows=[]
  for i,day in enumerate((26,25,24,22,17,16)):
   rows.append({'title':f'Can Oncu WorldSSP race news {i}','summary':'Can Oncu WorldSSP race','url':f'https://example.test/oncu{i}','published_at':f'2026-09-{day:02d}T10:00:00+00:00','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Oncu'})
  from datetime import datetime,timezone
  out=a.turkish_five_preview(rows,datetime(2026,9,26,12,0,tzinfo=timezone.utc),10)
  assert len(out)==5
  import json
  session=json.loads(a.TURKISH_SESSION.read_text(encoding='utf-8'))
  assert session['window_used_days']==10
  assert any('5 von 5' in m for m in sent)
  assert recv.turkish_selection('turkish 1, 3,5')==[1,3,5]
  assert recv.turkish_selection('turkish alle')==[1,2,3,4,5]
  assert recv.turkish_selection('turkish nein')==[]
  assert recv.selection('motogp 1')==[1]
  assert recv.selection('motogp 2')==[2]
  assert recv.selection('motogp 1-4')==[1,2,3,4]
  assert recv.selection('motogp 1 - 4')==[1,2,3,4]
  assert recv.selection('motogp 1-3,5')==[1,2,3,5]
  assert recv.selection('motogp 4-1') is None
  assert recv.selection('motogp 6') is None
  assert recv.turkish_selection('T1')==[1]
  assert recv.turkish_selection('t2')==[2]
  assert recv.turkish_selection('T1,T3,T5')==[1,3,5]
  assert recv.turkish_selection('T1, T3')==[1,3]
  assert recv.turkish_selection('T alle')==[1,2,3,4,5]
  assert recv.turkish_selection('T nein')==[]
  assert recv.turkish_selection('T ✅')==[1,2,3,4,5]
  assert recv.turkish_selection('T ❌')==[]
  assert recv.turkish_selection('turkish T1,T4')==[1,4]
  assert recv.turkish_selection('turkish 12')==[12]
  assert recv.turkish_selection('T12,T17')==[12,17]
  assert recv.turkish_selection('turkish 20')==[20]
  assert recv.turkish_selection('T1')==[1]
  assert recv.turkish_selection('T2')==[2]
  assert recv.turkish_selection('T1-4')==[1,2,3,4]
  assert recv.turkish_selection('T 1-4')==[1,2,3,4]
  assert recv.turkish_selection('turkish 1-4')==[1,2,3,4]
  assert recv.turkish_selection('T1-T4')==[1,2,3,4]
  assert recv.turkish_selection('T1-4,T7,T10-12')==[1,2,3,4,7,10,11,12]
  assert recv.turkish_selection('T4-1') is None
  assert recv.turkish_selection('turkish 21') is None
  assert recv.turkish_list_requested('turkish liste')
  assert recv.turkish_selection('motogp 1') is None
 finally:
  a.send_message=old_send;a.send_photo=old_photo;a.extract_og_image_url=old_og;a.roster_names=old_roster;a._send_turkish_source_photo=old_sender


def test_turkish_lane_owns_relevance_but_keeps_truth_guard():
 class FakeAgency:
  @staticmethod
  def series_for(x): return 'WorldSSP'
  @staticmethod
  def riders_in(text): return ['Can Öncü'] if 'oncu' in tqm.fold(text) else []
  @staticmethod
  def fact_whitelist_errors(x,caption): return []
  @staticmethod
  def language_sane(caption): return a.language_sane(caption)
 x={'title':'ALCOBA AT THE FRONT in WorldSSP','summary':'Jeremy Alcoba takes pole. Can Oncu is P6.','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'}
 good='🇹🇷 Can Öncü steht laut Quelle auf P6. Was sagt ihr dazu? 🏁\n\n#WorldSSP #CanOncu #BuelentsBikeLife #MotorradRacing'
 ok,errors=tqm.final_review(x,good,FakeAgency)
 assert ok,errors
 bad='🇹🇷 Can Öncü gewinnt das Rennen. Was sagt ihr dazu? 🏁\n\n#WorldSSP #CanOncu #BuelentsBikeLife #MotorradRacing'
 # A real agency whitelist is responsible for unsupported claims; this unit verifies
 # the Turkish rider itself is accepted as a supported perspective.
 assert tqm._target_supported(x)
 assert 'coole Socke' in tqm._prompt(x,FakeAgency)
 assert 'spontan, menschlich, mitfiebernd' in tqm._prompt(x,FakeAgency)
 assert 'Community-Frage ist erlaubt, aber nicht Pflicht' in tqm._prompt(x,FakeAgency)
 assert 'Keine erfundenen persoenlichen Erlebnisse' in tqm._prompt(x,FakeAgency)
 src=inspect.getsource(recv.handle_turkish)
 assert 'turkish_lane.process_manual_selection' in src and 'agency.qualify_copy(x)' not in src
 assert 'install_v855_hardening(agency)' in src
 qsrc=inspect.getsource(tqm.qualify)
 assert 'TURKISH FINAL-QM BLOCK attempt=' in qsrc
 assert 'TURKISH SEMANTIC-QM BLOCK attempt=' in qsrc
 assert 'TURKISH LANGUAGE-QM BLOCK attempt=' in qsrc
 from racing_v855_hardening import install as _install
 import motogp_content_agency_v2 as _production_agency
 _install(_production_agency)
 assert callable(_production_agency.fact_whitelist_errors)
 alias_item={'title':'ALCOBA AT THE FRONT WorldSSP','summary':'Alcoba takes pole, ahead of title rival Oncu in P6','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'}
 _production_agency.lock_source_series(alias_item,'WorldSSP')
 alias_errors=_production_agency.fact_whitelist_errors(alias_item,'Can Öncü ist laut Quelle P6.\n\n#WorldSSP #CanOncu')
 assert not any('Fahrer nicht in Quelle: Can Oncu' in e or 'Fahrer nicht in Quelle: Can Öncü' in e for e in alias_errors),alias_errors

def test_turkish_top20_history_keeps_preview_compact():
 sent=[];old_send=a.send_message;old_photo=a.send_photo;old_og=a.extract_og_image_url;old_roster=a.roster_names;old_sender=a._send_turkish_source_photo
 try:
  a.send_message=lambda m:sent.append(m);a.send_photo=lambda *args,**kwargs:None;a.extract_og_image_url=lambda u:'';a.roster_names=lambda:[];a._send_turkish_source_photo=lambda og,caption:False
  rows=[{'title':f'Can Öncü WorldSSP race result {i}','summary':'Can Öncü WorldSSP race','url':f'https://example.test/history{i}','published_at':'2026-09-26T10:00:00+00:00','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'} for i in range(20)]
  from datetime import datetime,timezone
  visible=a.turkish_five_preview(rows,datetime(2026,9,26,12,0,tzinfo=timezone.utc),10)
  assert len(visible)==5
  import json
  session=json.loads(a.TURKISH_SESSION.read_text(encoding='utf-8'))
  assert session['count']==20
  assert len(session['items'])==20
  assert session['items'][-1]['n']==20
  assert any('turkish liste' in m for m in sent)
 finally:
  a.send_message=old_send;a.send_photo=old_photo;a.extract_og_image_url=old_og;a.roster_names=old_roster;a._send_turkish_source_photo=old_sender


def test_turkish_range_dispatches_all_selected_items():
 rows={n:{'n':n,'title':f'Rider story {n}','url':f'https://example.test/{n}','summary':'Can Öncü WorldSSP','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'} for n in range(1,5)}
 old_rows=recv.parse_turkish_session;old_already=recv.already;old_chat=recv.get_chat_id;old_active=recv._active_batch;old_publish=recv.publish;old_send=recv.send_message
 import sys,types
 fake_agency=types.SimpleNamespace(lock_source_series=lambda *a,**k:None,enrich_turkish=lambda *a,**k:None,mark_priority=lambda *a,**k:None)
 def fake_process(x,n,a,max_attempts=3):
  x.update(instagram_media=f'img{n}.jpg',caption=f'caption {n}',caption_final=True)
  return {'status':'PASS','reasons':[],'item':x}
 fake_lane=types.SimpleNamespace(process_manual_selection=fake_process)
 old_agency=sys.modules.get('motogp_content_agency_v2');old_lane=sys.modules.get('turkish_editor_qm')
 captured={}
 try:
  recv.parse_turkish_session=lambda:rows;recv.already=lambda uid:False;recv.get_chat_id=lambda:'123';recv._active_batch=lambda:'batch'
  recv.send_message=lambda m:None
  recv.publish=lambda posts,chosen,uid,batch:(captured.update(chosen=list(chosen),posts=sorted(posts)) or len(chosen)*2)
  sys.modules['motogp_content_agency_v2']=fake_agency;sys.modules['turkish_editor_qm']=fake_lane
  # Hardening import happens inside handler; production module exists, but install must accept our fake.
  import racing_v855_hardening
  old_install=racing_v855_hardening.install;racing_v855_hardening.install=lambda a:None
  try: assert recv.handle_turkish(991,'123','T 1-4')
  finally: racing_v855_hardening.install=old_install
  assert captured['chosen']==[1,2,3,4],captured
  assert captured['posts']==[1,2,3,4],captured
 finally:
  recv.parse_turkish_session=old_rows;recv.already=old_already;recv.get_chat_id=old_chat;recv._active_batch=old_active;recv.publish=old_publish;recv.send_message=old_send
  if old_agency is not None:sys.modules['motogp_content_agency_v2']=old_agency
  if old_lane is not None:sys.modules['turkish_editor_qm']=old_lane


def test_turkish_visible_five_dedupes_racing_top5_and_backfills():
 sent=[];old_send=a.send_message;old_sender=a._send_turkish_source_photo;old_roster=a.roster_names
 try:
  a.send_message=lambda m:sent.append(m);a._send_turkish_source_photo=lambda og,caption:False;a.roster_names=lambda:[]
  rows=[{'title':f'Can Öncü WorldSSP story {i}','summary':'Can Öncü WorldSSP race','url':f'https://example.test/can-{i}','published_at':'2026-09-28T08:00:00+00:00','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'} for i in range(1,7)]
  racing=[dict(rows[1])]  # Same report is already visible in the normal Racing Top 5.
  from datetime import datetime,timezone
  visible=a.turkish_five_preview(rows,datetime(2026,9,28,10,0,tzinfo=timezone.utc),10,exclude_items=racing)
  assert len(visible)==5
  assert all(x['url']!=racing[0]['url'] for x in visible)
  assert rows[5]['url'] in {x['url'] for x in visible}  # next eligible report moved up
  import json
  session=json.loads(a.TURKISH_SESSION.read_text(encoding='utf-8'))
  assert all(x['url']!=racing[0]['url'] for x in session['items'])
 finally:
  a.send_message=old_send;a._send_turkish_source_photo=old_sender;a.roster_names=old_roster


def test_manual_turkish_redteam_never_promotes_fake_fact_to_pass():
 class FakeAgency:
  @staticmethod
  def lock_source_series(*args,**kwargs): pass
  @staticmethod
  def enrich_turkish(*args,**kwargs): pass
  @staticmethod
  def mark_priority(*args,**kwargs): pass
  @staticmethod
  def series_for(x): return 'WorldSSP'
  @staticmethod
  def language_sane(caption): return True
  @staticmethod
  def riders_in(text): return ['Can Öncü'] if 'oncu' in tqm.fold(text) else []
  @staticmethod
  def fact_whitelist_errors(x,caption):
   bad=[]
   low=caption.casefold()
   for token,label in [('99','Zahl'),('istanbul','Ort'),('ducati','Team'),('vertrag','Vertrag'),('motogp','Serie')]:
    if token in low: bad.append(f'{label} nicht in Quelle: {token}')
   return bad
  @staticmethod
  def semantic_review_detailed(x,caption): return {'hard_reasons':[],'repair_reasons':[],'language_ok':True}
  @staticmethod
  def prepare_media(x,i): return 'unused.jpg'
  @staticmethod
  def story_key(title,url): return 'story'

 x={'title':'Can Öncü WorldSSP update','summary':'Can Öncü beendet das Rennen auf P6.','url':'https://example.test/oncu','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'}
 old_edit=tqm.edit
 try:
  fake='Can Öncü gewinnt mit 99 Punkten in Istanbul für Ducati und unterschreibt einen Vertrag für MotoGP.\n\n#WorldSSP #CanOncu #BuelentsBikeLife'
  tqm.edit=lambda item,agency,reasons=None:(item.update(caption=fake) or fake)
  result=tqm.process_manual_selection(dict(x),1,FakeAgency,max_attempts=3)
  assert result['status']=='ESCALATE',result
  assert result['item'].get('turkish_final_qm')!='PASS'
  assert any(('nicht in Quelle' in e) or ('FACT/SOURCE' in e) for e in result['reasons']),result
 finally:
  tqm.edit=old_edit


def test_manual_turkish_positive_control_can_reach_chief():
 class FakeAgency:
  @staticmethod
  def lock_source_series(*args,**kwargs): pass
  @staticmethod
  def enrich_turkish(*args,**kwargs): pass
  @staticmethod
  def mark_priority(*args,**kwargs): pass
  @staticmethod
  def series_for(x): return 'WorldSSP'
  @staticmethod
  def language_sane(caption): return True
  @staticmethod
  def riders_in(text): return ['Can Öncü'] if 'oncu' in tqm.fold(text) else []
  @staticmethod
  def fact_whitelist_errors(x,caption): return []
  @staticmethod
  def semantic_review_detailed(x,caption): return {'hard_reasons':[],'repair_reasons':[],'language_ok':True}
  @staticmethod
  def prepare_media(x,i): return 'unused.jpg'
  @staticmethod
  def story_key(title,url): return 'story'
 x={'title':'Can Öncü WorldSSP update','summary':'Can Öncü beendet das Rennen auf P6.','url':'https://example.test/oncu','series':'WorldSSP','source_series':'WorldSSP','turkish_rider':'Can Öncü'}
 old_edit=tqm.edit;old_chief=tqm.chief_review;old_guard=tqm.final_guard_review
 try:
  good='Can Öncü beendet das Rennen laut Quelle auf P6. 🏁 Stark gekämpft! 💪 Was sagt ihr dazu?\n\n#WorldSSP #CanOncu #BuelentsBikeLife'
  tqm.edit=lambda item,agency,reasons=None:(item.update(caption=good) or good)
  tqm.final_guard_review=lambda item,caption:(True,[])
  tqm.chief_review=lambda *args,**kwargs:(True,[])
  result=tqm.process_manual_selection(dict(x),1,FakeAgency,max_attempts=3)
  assert result['status']=='PASS',result
  assert result['item']['turkish_final_qm']=='PASS'
  assert result['item']['caption_final'] is True
 finally:
  tqm.edit=old_edit;tqm.chief_review=old_chief;tqm.final_guard_review=old_guard



def test_turkish_target_lock_blocks_other_rider_in_real_toprak_pattern():
 class FakeAgency:
  @staticmethod
  def series_for(x): return 'MotoGP'
  @staticmethod
  def riders_in(text):
   out=[]
   for n in ('Toprak Razgatlıoğlu','Jorge Martin','Marc Márquez','Marco Bezzecchi','Pedro Acosta'):
    if tqm.fold(n) in tqm.fold(text): out.append(n)
   return out
  @staticmethod
  def fact_whitelist_errors(x,caption): return []
  @staticmethod
  def language_sane(caption): return True
 x={'title':"MotoGP Avusturya Sprint: Martin'den İnanılmaz Zafer, Toprak Razgatlıoğlu'ndan Güçlü Performans!",
    'summary':'Jorge Martin kazandı. Marc Márquez ikinci. Toprak Razgatlıoğlu güçlü performans gösterdi.',
    'series':'MotoGP','source_series':'MotoGP','turkish_rider':'Toprak Razgatlıoğlu'}
 drift='Jorge Martin gewinnt den Sprint. Toprak Razgatlıoğlu zeigt eine starke Leistung. 🏁'
 errs=tqm._target_focus_errors(x,drift,FakeAgency)
 assert any('Jorge Martin' in e for e in errs),errs
 focused='Toprak Razgatlıoğlu zeigt laut Quelle eine starke Leistung. 🇹🇷🏁'
 assert tqm._target_focus_errors(x,focused,FakeAgency)==[]
 prompt=tqm._prompt(x,FakeAgency)
 assert 'TARGET-LOCK' in prompt and 'ausschliesslich von Toprak Razgatlıoğlu' in prompt


def test_racing_number_guard_does_not_extract_numeric_suffix_from_alphanumeric_token():
 import racing_v855_hardening as hard
 class FakeAgency:
  RIDERS_V2=[]
  @staticmethod
  def fold(s): return tqm.fold(s)
  @staticmethod
  def riders_in(s): return []
  @staticmethod
  def _editor_prompt(*args,**kwargs): return ''
  @staticmethod
  def semantic_review_detailed(*args,**kwargs): return {'hard_reasons':[],'repair_reasons':[],'language_ok':True}
 agency=FakeAgency()
 hard.install(agency)
 x={'title':'Oğuz Taşhan Avrupa Şampiyonu','summary':'Oğuz Taşhan Avrupa Şampiyonu','series':'MotoGP','source_series':'MotoGP'}
 errs=agency.fact_whitelist_errors(x,'Oğuz Taşhan A00 gibi bir kod olmadan harika bir gün yaşadı. #MotoGP')
 assert not any(e.endswith('Zahl nicht in Quelle: 00') for e in errs),errs


def test_source_entity_guard_does_not_treat_aktion_as_place():
 from racing_source_entity_guard import errors
 x={'title':'Oğuz Taşhan Avrupa Şampiyonu','summary':'Oğuz Taşhan feiert den Titel.'}
 assert not any('Ort nicht in Quelle: Aktion' in e for e in errors(x,'Oğuz Taşhan ist in Aktion und wir feiern mit!'))


def test_turkish_german_place_alias_and_fuer_idiom_do_not_false_block():
 from racing_source_entity_guard import errors
 x={'title':'MotoGP Avusturya Sprint: Toprak Razgatlıoğlu güçlü performans','summary':'Toprak Razgatlıoğlu Avusturya Sprint yarışında sürdü.'}
 e=errors(x,'Toprak Razgatlıoğlu sorgt in Österreich für Aufsehen.')
 assert not any('Österreich' in z or 'Aufsehen' in z for z in e),e
 e=errors(x,'Toprak Razgatlıoğlu fährt in Mugello.')
 assert any('Mugello' in z for z in e),e


def test_turkish_language_failure_always_has_actionable_reason():
 src=inspect.getsource(tqm.process_manual_selection)
 assert 'keine Detailgruende vom Semantic-QM geliefert' in src


def test_motogp_geo_lexicon_keeps_austria_and_australia_distinct():
 from racing_geo_lexicon import RACE_GEO
 assert 'Avusturya' in RACE_GEO['Österreich']['tr']
 assert 'Avustralya' in RACE_GEO['Australien']['tr']
 assert set(RACE_GEO['Österreich']['tr']).isdisjoint(set(RACE_GEO['Australien']['tr']))
 from racing_source_entity_guard import errors
 assert not errors({'title':'MotoGP Avusturya Sprint','summary':'Spielberg'},'Toprak fährt in Österreich.')
 assert not errors({'title':'MotoGP Avustralya GP','summary':'Adelaide'},'Toprak fährt in Australien.')
 assert any('Australien' in e for e in errors({'title':'MotoGP Avusturya Sprint','summary':'Spielberg'},'Toprak fährt in Australien.'))


def test_turkish_preview_uses_saved_preview_when_live_og_missing():
 import motogp_content_agency_v2 as agency
 src=inspect.getsource(agency.turkish_five_preview)
 assert "extract_og_image_url(source) or x.get('preview','')" in src
 assert 'Quell-Vorschaubild nicht abrufbar' in src


def test_live_turkish_bad_copy_patterns_are_forbidden_by_editor_contract():
 class A:
  def series_for(self,x):return 'European SSP300 Cup'
 p=tqm._prompt({'turkish_rider':'Oğuz Taşhan','title':'Oğuz Taşhan Avrupa Şampiyonu','summary':'Oğuz Taşhan European SSP300 Cup şampiyonu.','url':'https://example.test'},A())
 for bad in ('harte Kaempfe','Podium','ganzes Feld hinter sich gelassen','dicht hinter Spitzenfahrern','Fans jubeln','ernstzunehmender Anwaerter'):
  assert bad in p
 assert '2-4 Saetze' in p and 'KEIN anderer Fahrername' in p


def test_escalated_turkish_items_have_per_item_source_preview_path():
 import motogp_telegram_receive_v85 as recv
 src=inspect.getsource(recv.handle_turkish)
 assert 'Quell-Vorschau T{pn}' in src
 assert 'px.get("preview","")' in src


def test_turkish_empty_semantic_language_diagnostic_is_not_valid_language_feedback():
 src=inspect.getsource(tqm.process_manual_selection)
 assert 'Semantic-QM meldet language_ok=false ohne konkreten repair_reason' in src
 assert 'keine Detailgruende vom Semantic-QM geliefert' not in src


def test_escalated_preview_uses_url_download_helper_not_local_path_send():
 import motogp_telegram_receive_v85 as recv
 src=inspect.getsource(recv.handle_turkish)
 assert 'agency._send_turkish_source_photo(preview,label)' in src
 assert 'send_photo(preview' not in src

if __name__=='__main__':
 test_turkish_range_dispatches_all_selected_items();test_turkish_visible_five_dedupes_racing_top5_and_backfills()
 test_manual_turkish_redteam_never_promotes_fake_fact_to_pass();test_manual_turkish_positive_control_can_reach_chief();test_turkish_target_lock_blocks_other_rider_in_real_toprak_pattern();test_racing_number_guard_does_not_extract_numeric_suffix_from_alphanumeric_token();test_source_entity_guard_does_not_treat_aktion_as_place();test_turkish_german_place_alias_and_fuer_idiom_do_not_false_block();test_turkish_language_failure_always_has_actionable_reason();test_motogp_geo_lexicon_keeps_austria_and_australia_distinct();test_turkish_preview_uses_saved_preview_when_live_og_missing();test_live_turkish_bad_copy_patterns_are_forbidden_by_editor_contract();test_escalated_turkish_items_have_per_item_source_preview_path();test_turkish_empty_semantic_language_diagnostic_is_not_valid_language_feedback();test_escalated_preview_uses_url_download_helper_not_local_path_send();test_priority_marking_and_order();test_top20_priority();test_central_turkish_rider_source_registry();test_surname_only_turkish_riders_use_series_context();test_rider_centered_scout_uses_registered_official_sources();test_tmf_haberler_links_are_discovered_and_generic_titles_are_not_people();test_turkish_discovery_memory_does_not_auto_promote();test_turkish_candidate_is_independent_and_deduplicated();test_turkish_preview_is_separate_and_limited();test_turkish_ten_day_window_and_selection_parser();test_turkish_lane_owns_relevance_but_keeps_truth_guard();test_turkish_top20_history_keeps_preview_compact()
 print('RACING PRIORITY + TURKISH FIVE REGRESSION: PASS')



