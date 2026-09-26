import turkish_riders_scout as scout
import motogp_content_agency_v2 as agency

urls=dict(scout.TURKISH_MEDIA_SOURCES)
assert urls['MotoEtkinlikcom']=='https://www.instagram.com/motoetkinlikcom/'
assert urls['MotoEtkinlikRacing']=='https://www.instagram.com/motoetkinlikracing/'
assert urls['TurkiyeSBK']=='https://www.instagram.com/turkiyesbk/'
for text,expected in [
 ('Toprak Razgatlioglu yeni haber','Toprak Razgatlıoğlu'),
 ('Can Oncu WorldSSP','Can Öncü'),
 ('Deniz Oncu Moto2','Deniz Öncü'),
]:
 assert scout.rider_for(text)==expected,(text,scout.rider_for(text))
 assert agency.detect_turkish_rider({'title':text,'summary':'','url':''})==expected
print('TEST – Turkish Media Sources: PASS')

for rider in ('Toprak Razgatlıoğlu','Can Öncü','Deniz Öncü','Bahattin Sofuoğlu'):
 ctx=scout.RIDER_SOURCES[rider]
 assert ctx.get('rider_group')=='KNN54 Riders',rider
 assert ctx.get('mentor_manager')=='Kenan Sofuoğlu',rider


# Regression: social indexed posts accept /p/ and /reel/ and never use media label as series.
class Resp:
 def __init__(self,text): self.text=text
 def raise_for_status(self): pass
old_get=scout.requests.get
try:
 scout.requests.get=lambda *a,**k: Resp('<a href="https://www.instagram.com/motoetkinlikcom/p/ABC123/">Toprak Razgatlioglu MotoGP yeni haber</a><a href="https://www.instagram.com/turkiyesbk/reel/XYZ789/">Can Oncu WorldSSP yarisi</a>')
 rows=scout._search_fallback('MotoEtkinlikcom','https://www.instagram.com/motoetkinlikcom/',20)
 assert any('/p/' in r[1] and r[3]=='Toprak Razgatlıoğlu' for r in rows),rows
finally:
 scout.requests.get=old_get

# Media source names are discovery labels, never championship values.
assert 'MotoEtkinlikcom' not in {ctx.get('series') for ctx in scout.RIDER_SOURCES.values()}
print('TEST – Turkish Social 429 Fallback: PASS')


# Open Turkish web lane: .tr/.com.tr sources and registry-driven rider resolution.
web=dict(scout.TURKISH_WEB_SOURCES)
assert web['TMF'].endswith('.org.tr/Haberler/')
assert 'aa.com.tr' in web['AnadoluAjansi']
class WebResp:
 def __init__(self,text): self.text=text
 def raise_for_status(self): pass
old_get=scout.requests.get
try:
 scout.requests.get=lambda url,**k: WebResp('<a href="/Haberler/Can-oncu-Guncel/">Can Öncü Dünya Supersport Şampiyonası güncel yarış haberi</a>')
 rows=scout.turkish_web_scout(20)
 assert any(r[2]=='Can Öncü' for r in rows),rows
 assert all(r[3] not in ('TMF','AnadoluAjansi') for r in rows),rows
finally:
 scout.requests.get=old_get
print('TEST – Turkish Open Web Scout: PASS')

# AA uses /tr/spor/<slug>/<numeric-id>, not TMF's /Haberler/ route.
old_get=scout.requests.get
try:
 def aa_page(url,**kwargs):
  if 'aa.com.tr' not in url:return WebResp('')
  return WebResp('''
   <a href="/tr/spor/can-oncu-yarisa-hazir/1234567">Can Öncü Dünya Supersport yarışına hazır</a>
   <a href="/tr/spor">Can Öncü spor haberleri kategorisi</a>
   <a href="https://example.org/tr/spor/can-oncu/1234567">Can Öncü Dünya Supersport yarışına hazır</a>
  ''')
 scout.requests.get=aa_page
 rows=scout.turkish_web_scout(20)
 assert len(rows)==1,rows
 assert rows[0][1]=='https://www.aa.com.tr/tr/spor/can-oncu-yarisa-hazir/1234567',rows
 assert rows[0][2:] == ('Can Öncü','WorldSSP'),rows
finally:
 scout.requests.get=old_get
