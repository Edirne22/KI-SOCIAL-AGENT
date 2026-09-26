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
  assert any('5 von 5' in m for m in sent)
  assert recv.turkish_selection('turkish 1, 3,5')==[1,3,5]
  assert recv.turkish_selection('turkish alle')==[1,2,3,4,5]
  assert recv.turkish_selection('turkish nein')==[]
  assert recv.turkish_selection('T1')==[1]
  assert recv.turkish_selection('t2')==[2]
  assert recv.turkish_selection('T1,T3,T5')==[1,3,5]
  assert recv.turkish_selection('T1, T3')==[1,3]
  assert recv.turkish_selection('T alle')==[1,2,3,4,5]
  assert recv.turkish_selection('T nein')==[]
  assert recv.turkish_selection('T ✅')==[1,2,3,4,5]
  assert recv.turkish_selection('T ❌')==[]
  assert recv.turkish_selection('turkish T1,T4')==[1,4]
  assert recv.turkish_selection('motogp 1') is None
 finally:
  a.send_message=old_send;a.send_photo=old_photo;a.extract_og_image_url=old_og;a.roster_names=old_roster;a._send_turkish_source_photo=old_sender


def test_turkish_lane_owns_relevance_but_keeps_truth_guard():
 class FakeAgency:
  @staticmethod
  def series_for(x): return 'WorldSSP'
  @staticmethod
  def fact_whitelist_errors(x,caption): return []
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
 assert 'turkish_lane.qualify' in src and 'agency.qualify_copy(x)' not in src
 assert 'install_v855_hardening(agency)' in src
 qsrc=inspect.getsource(tqm.qualify)
 assert 'TURKISH FINAL-QM BLOCK attempt=' in qsrc
 assert 'TURKISH SEMANTIC-QM BLOCK attempt=' in qsrc
 assert 'TURKISH LANGUAGE-QM BLOCK attempt=' in qsrc
 from racing_v855_hardening import install as _install
 import motogp_content_agency_v2 as _production_agency
 _install(_production_agency)
 assert callable(_production_agency.fact_whitelist_errors)

if __name__=='__main__':
 test_priority_marking_and_order();test_top20_priority();test_surname_only_turkish_riders_use_series_context();test_turkish_candidate_is_independent_and_deduplicated();test_turkish_preview_is_separate_and_limited();test_turkish_ten_day_window_and_selection_parser();test_turkish_lane_owns_relevance_but_keeps_truth_guard()
 print('RACING PRIORITY + TURKISH FIVE REGRESSION: PASS')


