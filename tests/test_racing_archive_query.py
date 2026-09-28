import racing_archive_query as q

def rows():
    return [
      {"story_key":"motogp:a","title":"Toprak Razgatlioglu test","summary":"Toprak news","series":"MotoGP","turkish_rider":"Toprak Razgatlıoğlu","_pool_day":"2099-01-01"},
      {"story_key":"motogp:b","title":"Jack Miller update","summary":"Miller news","series":"MotoGP","turkish_rider":"","_pool_day":"2099-01-01"},
    ]

def test_rider_and_turkish_filters(monkeypatch):
    monkeypatch.setattr(q,"all_rows",rows)
    monkeypatch.setattr(q,"parse_days",lambda low:(None,"Archiv"))
    r,label=q.query("Zeig mir die türkischen Berichte")
    assert len(r)==1 and "Toprak" in r[0]["title"]
    r,label=q.query("Gibt es Neuigkeiten über Jack Miller?")
    assert len(r)==1 and "Jack Miller" in r[0]["title"]

def test_posting_status_filter(monkeypatch):
    monkeypatch.setattr(q,"all_rows",rows)
    monkeypatch.setattr(q,"parse_days",lambda low:(None,"Archiv"))
    monkeypatch.setattr(q,"published",lambda row: row["story_key"]=="motogp:a")
    r,_=q.query("Zeig mir nur ungepostete MotoGP Meldungen")
    assert [x["story_key"] for x in r]==["motogp:b"]
    r,_=q.query("Welche MotoGP Meldungen habe ich schon gepostet?")
    assert [x["story_key"] for x in r]==["motogp:a"]

def test_manual_shortcuts_delegate(monkeypatch):
    seen=[]
    monkeypatch.setattr(q.manual,"handle",lambda command: seen.append(command) or 1)
    assert q.handle("T17")==1
    assert seen[-1]=="racing artikel 17"
    assert q.handle("poste 4")==1
    assert seen[-1]=="racing artikel 4"
    assert q.handle("nimm 9")==1
    assert seen[-1]=="racing artikel 9"

def test_natural_query_detection():
    assert q.is_query("Was gab es gestern über Marc Márquez?")
    assert q.is_query("Gib mir die Berichte über Deniz Öncü")
    assert q.is_query("Neuigkeiten über Jack Miller?")
