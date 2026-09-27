import turkish_riders_scout as scout
import motogp_content_agency_v2 as agency

urls=dict(scout.TURKISH_MEDIA_SOURCES)
assert 'MotoEtkinlikcom' not in urls
assert 'MotoEtkinlikRacing' not in urls
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
 scout.requests.get=lambda *a,**k: Resp('<a href="https://www.instagram.com/turkiyesbk/reel/XYZ789/">Can Oncu WorldSSP yarisi</a>')
 rows=scout._search_fallback('TurkiyeSBK','https://www.instagram.com/turkiyesbk/',20)
 assert any('/reel/' in r[1] and r[3]=='Can Öncü' for r in rows),rows
finally:
 scout.requests.get=old_get

# Media source names are discovery labels, never championship values.
assert 'MotoEtkinlikcom' not in {ctx.get('series') for ctx in scout.RIDER_SOURCES.values()}
assert not any(name.startswith('MotoEtkinlik') for name,_ in scout.TURKISH_WEB_SOURCES)
assert not any(name.startswith('MotoEtkinlik') for name,_ in scout.TURKISH_MEDIA_SOURCES)
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


# Deep Turkish web search must discover a registered rider beyond portal front-page anchors.
class SearchResp:
 def __init__(self,text): self.text=text
 def raise_for_status(self): pass
old_get=scout.requests.get
try:
 def fake_get(url,**kwargs):
  if 'google.com/search' in url and ('Can' in url or 'Can%20' in url or 'Can%2B' in url):
   return SearchResp('<a href="https://spor.example.com.tr/motosiklet/can-oncu-cremona">Can Öncü Cremona WorldSSP yarış haberi</a>')
  return SearchResp('')
 scout.requests.get=fake_get
 deep=scout._turkish_web_search('Can Öncü',('Can Oncu',),20)
 assert deep and deep[0][3]=='Can Öncü',deep
 assert 'example.com.tr' in deep[0][1],deep
finally:
 scout.requests.get=old_get
print('TEST – Turkish Rider-Centered Web Search: PASS')


# Article links must not exhaust the crawl budget before a linked racing category.
old_get=scout.requests.get
try:
 class CrawlResp:
  def __init__(self,text):self.text=text
  def raise_for_status(self):pass
 def crawl_get(url,**kwargs):
  if url.endswith('/tr/spor'):
   football=''.join(
    f'<a href="/tr/spor/futbol/mac-{i}/{1000000+i}">Futbol derbisi mac haberi {i}</a>'
    for i in range(35)
   )
   return CrawlResp(football+'<a href="/tr/spor/motor-sporlari">Motor sporları haberleri</a>')
  if url.endswith('/tr/spor/motor-sporlari'):
   return CrawlResp('<a href="/tr/spor/motor-sporlari/can-oncu-cremona/9999999">Can Öncü Dünya Supersport yarış haberi</a>')
  return CrawlResp('')
 scout.requests.get=crawl_get
 crawled=scout._turkish_site_crawl('AnadoluAjansi','https://www.aa.com.tr/tr/spor',max_pages=30,depth=2)
 assert any(row[3]=='Can Öncü' for row in crawled),crawled
finally:
 scout.requests.get=old_get
print('TEST – Turkish Category Crawl Budget: PASS')


# Every configured specialist source needs its own real article URL pattern.
old_get=scout.requests.get
try:
 def specialist_get(url,**kwargs):
  if 'motoron.com.tr' in url:
   return CrawlResp('<a href="/motosiklet-haber/toprak-motogp-haberi/">Toprak Razgatlıoğlu MotoGP yarış haberi</a>')
  if 'tr.motorsport.com' in url:
   return CrawlResp('<a href="/motogp/news/toprak-yaris-aciklamasi/10999999/">Toprak Razgatlıoğlu MotoGP yarış açıklaması</a>')
  if 'trmotosports.com' in url:
   return CrawlResp('<a href="/toprak-razgatlioglu-motogp-haberi/">Toprak Razgatlıoğlu MotoGP yarış haberi</a>')
  if 'trf1.net' in url:
   return CrawlResp('<a href="/motor-sporlari/motogp/toprak-razgatlioglu-misano-motogp-yarisinda-12-oldu/113661/">Toprak Razgatlıoğlu Misano MotoGP yarış haberi</a>')
  return CrawlResp('')
 scout.requests.get=specialist_get
 motoron=scout._turkish_site_crawl('Motoron','https://www.motoron.com.tr/kategori/yarislar/')
 motorsport=scout._turkish_site_crawl('MotorsportTR','https://tr.motorsport.com/')
 trmotosports=scout._turkish_site_crawl('TRMotoSports','https://www.trmotosports.com/')
 trf1=scout._turkish_site_crawl('TRF1MotoGP','https://trf1.net/motor-sporlari/motogp/')
 assert motoron and motoron[0][3]=='Toprak Razgatlıoğlu',motoron
 assert motorsport and motorsport[0][3]=='Toprak Razgatlıoğlu',motorsport
 assert trmotosports and trmotosports[0][3]=='Toprak Razgatlıoğlu',trmotosports
 assert trf1 and trf1[0][3]=='Toprak Razgatlıoğlu',trf1
finally:
 scout.requests.get=old_get
print('TEST – Turkish Specialist Article Routes: PASS')


# Pagination regression: category -> page 2 -> hidden registered-rider article.
old_get=scout.requests.get
try:
 def paged_get(url,**kwargs):
  if url.rstrip('/')=='https://www.motoron.com.tr/kategori/yarislar':
   return CrawlResp('<a href="/kategori/yarislar/page/2/">Sonraki yarış haberleri sayfası</a>')
  if '/kategori/yarislar/page/2' in url:
   return CrawlResp('<a href="/motosiklet-haber/can-oncu-worldssp/">Can Öncü WorldSSP podyum yarış haberi</a>')
  return CrawlResp('')
 scout.requests.get=paged_get
 rows=scout._turkish_site_crawl('Motoron','https://www.motoron.com.tr/kategori/yarislar/',max_pages=5,depth=2)
 assert any(r[3]=='Can Öncü' and '/motosiklet-haber/' in r[1] for r in rows),rows
finally:
 scout.requests.get=old_get
print('TEST – Turkish Pagination Crawl: PASS')


# A bare pagination route must be recognized by the pagination regex itself.
old_get=scout.requests.get
try:
 def bare_paged_get(url,**kwargs):
  if '/page/2/' in url:
   return CrawlResp('<a href="/toprak-pagination-yaris-haberi/">Toprak Razgatlıoğlu MotoGP yarış sonucu</a>')
  return CrawlResp('<a href="/page/2/">Sonraki yarış haberleri</a>')
 scout.requests.get=bare_paged_get
 bare_paged=scout._turkish_site_crawl('TRMotoSports','https://www.trmotosports.com/',depth=2)
 assert bare_paged and bare_paged[0][3]=='Toprak Razgatlıoğlu',bare_paged
finally:
 scout.requests.get=old_get
print('TEST – Turkish Bare Pagination Route: PASS')


# MotorsportTR hardening: dead series navigation shells must not be requested.
old_get=scout.requests.get
try:
 requested=[]
 def motorsport_nav_get(url,**kwargs):
  requested.append(url)
  if url=='https://tr.motorsport.com/':
   return CrawlResp('''
    <a href="/moto3/">Moto3 haberleri ve sonuçları</a>
    <a href="/moto3/news/">Moto3 son haberler ve gelişmeler</a>
    <a href="/moto3/schedule/">Moto3 yarış takvimi ve saatleri</a>
    <a href="/motogp/news/toprak-guncel/10999999/">Toprak Razgatlıoğlu MotoGP güncel yarış haberi</a>
   ''')
  return CrawlResp('')
 scout.requests.get=motorsport_nav_get
 rows=scout._turkish_site_crawl('MotorsportTR','https://tr.motorsport.com/',max_pages=10,depth=2)
 assert len(requested)==1,requested
 assert rows and rows[0][3]=='Toprak Razgatlıoğlu',rows
finally:
 scout.requests.get=old_get
print('TEST – MotorsportTR Dead Navigation Filter: PASS')


# Production regression: Turkish WSSP source must lock to WorldSSP, never Moto2.
wssp={'title':'WSSP Superpole İtalya: Alcoba Cremona’da, Kawasaki 2021’den sonra ilk kez zirvede, Can Öncü 6. sırada bitirdi','summary':'','url':'https://tr.motorsport.com/supersport/news/example/10859078','series':'Moto2','source_series':'Moto2','series_locked':True}
agency.lock_source_series(wssp)
assert agency.series_for(wssp)=='WorldSSP',wssp
assert wssp['source_series']=='WorldSSP',wssp

# German final text must not leak common Turkish result phrases.
assert not agency.language_sane('Can Öncü kam in Cremona puansız an.'), 'Turkish leakage accepted'
assert agency.language_sane('Can Öncü blieb in Cremona ohne Punkte.'), 'Valid German rejected'
print('TEST – Turkish Series + German Language Hardening: PASS')


# MotoEtkinlik discovery is owned by the dedicated adapter, not generic site crawling.
from motoetkinlik_source import NEWS_ENDPOINTS,REFERENCE_ENDPOINTS
assert NEWS_ENDPOINTS['MotoGP']=='https://motoetkinlik.com/kategori/motogp/'
assert NEWS_ENDPOINTS['Moto2']=='https://motoetkinlik.com/kategori/moto2/'
assert NEWS_ENDPOINTS['Moto3']=='https://motoetkinlik.com/kategori/moto3/'
assert NEWS_ENDPOINTS['WorldSBK']=='https://motoetkinlik.com/kategori/wsbk/'
assert NEWS_ENDPOINTS['Racing']=='https://motoetkinlik.com/kategori/yaris/'
assert NEWS_ENDPOINTS['Video']=='https://motoetkinlik.com/kategori/youtube/'
assert REFERENCE_ENDPOINTS['results'].endswith('/motogp-yaris-sonuclari/')
assert REFERENCE_ENDPOINTS['standings'].endswith('/motogp-puan-durumu/')
assert REFERENCE_ENDPOINTS['riders'].endswith('/motogp-suruculeri/')
assert REFERENCE_ENDPOINTS['calendar'].endswith('/motogp-yaris-takvimi/')
from turkish_riders_scout_adapter import turkish_web_scout as adapter_web_scout
assert agency.turkish_web_scout is adapter_web_scout
print('TEST – MotoEtkinlik Dedicated Adapter Contract: PASS')

# Production regression 2026-09-27: Turkish prose may be source material but never final German copy.
assert agency.turkish_language_leak("2026’da Yarışmayı Bırakmayı Düşündüm")
assert not agency.language_sane("2026’da Yarışmayı Bırakmayı Düşündüm\n\nToprak Razgatlıoğlu vergleicht seine Saison.")
assert agency.language_sane("Toprak Razgatlıoğlu vergleicht seine erste MotoGP-Saison mit 2018.")
assert agency.language_sane("Can Öncü startet aus der sechsten Position.")
assert 'QUESTION_HOOK_BODY' not in [agency.choose_structure_variant() for _ in range(100)]
print('TEST – MotoEtkinlik + Turkish German Localization: PASS')
