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
