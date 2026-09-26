"""Regression: priority repair lane + independent Turkish-five preview."""
import motogp_content_agency_v2 as a

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

def test_turkish_preview_is_separate_and_limited():
 sent=[]
 old_send=a.send_message;old_roster=a.roster_names
 try:
  a.send_message=lambda m:sent.append(m)
  a.roster_names=lambda:[]
  rows=[]
  for i in range(7):
   rows.append({'title':f'Toprak Razgatlioglu race news {i}','summary':'Toprak Razgatlioglu racing','url':f'https://example.test/tr{i}','published_at':'2026-09-26T10:00:00+00:00','series':'WorldSBK','source_series':'WorldSBK','turkish_rider':'Toprak Razgatlioglu'})
  from datetime import datetime,timezone
  out=a.turkish_five_preview(rows,datetime(2026,9,26,12,0,tzinfo=timezone.utc))
  assert len(out)==5
  assert len(sent)==1
  assert 'NICHT automatisch freigegeben' in sent[0]
  assert 'T5' in sent[0] and 'T6' not in sent[0]
 finally:
  a.send_message=old_send;a.roster_names=old_roster

if __name__=='__main__':
 test_priority_marking_and_order();test_top20_priority();test_turkish_preview_is_separate_and_limited()
 print('RACING PRIORITY + TURKISH FIVE REGRESSION: PASS')
