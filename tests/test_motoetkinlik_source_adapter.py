import motoetkinlik_source as m

expected_news={
 "MotoGP":"https://motoetkinlik.com/kategori/motogp/",
 "Moto2":"https://motoetkinlik.com/kategori/moto2/",
 "Moto3":"https://motoetkinlik.com/kategori/moto3/",
 "WorldSBK":"https://motoetkinlik.com/kategori/wsbk/",
 "WorldSSP":"https://motoetkinlik.com/kategori/worldssp/",
 "Racing":"https://motoetkinlik.com/kategori/yaris/",
 "Video":"https://motoetkinlik.com/kategori/youtube/",
}
assert m.NEWS_ENDPOINTS==expected_news
assert m.REFERENCE_ENDPOINTS["results"]=="https://motoetkinlik.com/motogp-yaris-sonuclari/"
assert m.REFERENCE_ENDPOINTS["standings"]=="https://motoetkinlik.com/motogp-puan-durumu/"
assert m.REFERENCE_ENDPOINTS["riders"]=="https://motoetkinlik.com/motogp-suruculeri/"
assert m.REFERENCE_ENDPOINTS["calendar"]=="https://motoetkinlik.com/motogp-yaris-takvimi/"

assert m.endpoint_kind(expected_news["Racing"])=="news"
assert m.endpoint_kind(m.REFERENCE_ENDPOINTS["riders"])=="riders"

fixture='''<html><body>
<a href="/kategori/yaris/">Yarış</a>
<a href="/motogp-puan-durumu/">MotoGP Puan Durumu</a>
<a href="/toprak-avusturya-motogp-haberi/">Toprak Razgatlıoğlu Avusturya MotoGP yarış haberi</a>
<a href="https://example.com/bad/">External racing article that must not enter</a>
</body></html>'''
rows=m.discover_news(fetch=lambda url: fixture,limit_per_endpoint=20)
urls={r["url"] for r in rows}
assert "https://motoetkinlik.com/toprak-avusturya-motogp-haberi/" in urls
assert "https://motoetkinlik.com/kategori/yaris/" not in urls
assert "https://motoetkinlik.com/motogp-puan-durumu/" not in urls
assert not any("example.com" in u for u in urls)
assert all(r["source_endpoint"].startswith("https://motoetkinlik.com/kategori/") for r in rows)

refs=m.reference_snapshots(fetch=lambda url:"<h1>Toprak</h1><p>7 Prima Pramac Yamaha</p>")
assert set(refs)=={"results","standings","riders","calendar"}
assert refs["riders"]["url"]==m.REFERENCE_ENDPOINTS["riders"]
assert "Toprak" in refs["riders"]["text"]
print("TEST – MotoEtkinlik Source Adapter: PASS")



def test_general_racing_editorial_lane_keeps_non_turkish_motogp(monkeypatch):
 import turkish_riders_scout_adapter as a
 fixture_rows=[
  {"title":"Ai Ogura returns to MotoGP action in Austria","url":"https://motoetkinlik.com/ai-ogura-avusturya-motogp-donus/","series":"MotoGP","source":"MotoEtkinlik"},
  {"title":"Alex Rins Spielberg MotoGP weekend update","url":"https://motoetkinlik.com/alex-rins-spielberg-motogp/","series":"MotoGP","source":"MotoEtkinlik"},
 ]
 monkeypatch.setattr(a,"discover_news",lambda limit_per_endpoint=120: fixture_rows)
 monkeypatch.setattr(a._legacy,"TURKISH_WEB_SOURCES",())
 rows=a.racing_editorial_scout(120)
 assert [r[0] for r in rows]==[x["title"] for x in fixture_rows]
 assert all(r[2]=="MotoGP" and r[3]=="MotoEtkinlik" for r in rows)
 # Regression: this general lane must not require Turkish rider registration.
 assert all(a._legacy.rider_for(r[0]+" "+r[1],r[2])=="" for r in rows)

def test_motoetkinlik_category_path_contract():
 assert m.NEWS_ENDPOINTS["MotoGP"]=="https://motoetkinlik.com/kategori/motogp/"
 assert "/kategori/" in m.NEWS_ENDPOINTS["MotoGP"]
