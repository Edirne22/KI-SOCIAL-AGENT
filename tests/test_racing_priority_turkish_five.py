"""Regression: priority repair lane + independent Turkish-five preview."""
import motogp_content_agency_v2 as a
import turkish_riders_scout as trs

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

if __name__=='__main__':
 test_priority_marking_and_order();test_top20_priority();test_surname_only_turkish_riders_use_series_context();test_turkish_candidate_is_independent_and_deduplicated();test_turkish_preview_is_separate_and_limited()
 print('RACING PRIORITY + TURKISH FIVE REGRESSION: PASS')
