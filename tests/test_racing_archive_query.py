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


def test_natural_top_lists_paginate_without_repeating(monkeypatch,tmp_path):
    state=tmp_path/"state.json"; monkeypatch.setattr(q,"STATE",state)
    data=[{"story_key":str(i),"title":"Story "+str(i),"series":"MotoGP","url":"https://example.test/"+str(i)} for i in range(20)]
    sent=[]; monkeypatch.setattr(q,"all_rows",lambda:data); monkeypatch.setattr(q,"send_message",sent.append)
    monkeypatch.setattr(q,"published",lambda row:False)
    assert q.handle("Zeig mir die Top 10")==10
    saved=__import__("json").loads(state.read_text(encoding="utf-8"))
    assert saved["offset"]==10 and len(saved["rows"])==10
    sent.clear()
    assert q.handle("Gib mir die Top 20 Berichte")==20
    saved=__import__("json").loads(state.read_text(encoding="utf-8"))
    assert saved["offset"]==10 and len(saved["rows"])==20
    rendered="\n".join(sent)
    assert "1." in rendered and "10." in rendered and "11." not in rendered
    sent.clear()
    assert q.handle("mehr")==10
    assert "11." in sent[-1] and "20." in sent[-1]

def test_more_uses_active_session(monkeypatch,tmp_path):
    state=tmp_path/"state.json"; monkeypatch.setattr(q,"STATE",state)
    data=[{"story_key":str(i),"title":"Story "+str(i),"series":"MotoGP","url":"https://example.test/"+str(i)} for i in range(20)]
    state.write_text(__import__("json").dumps({"label":"Top 20","rows":data,"offset":10}),encoding="utf-8")
    sent=[]; monkeypatch.setattr(q,"send_message",sent.append); monkeypatch.setattr(q,"published",lambda row:False)
    assert q.handle("mehr")==10
    saved=__import__("json").loads(state.read_text(encoding="utf-8"))
    assert saved["offset"]==20
    assert "11." in sent[-1] and "20." in sent[-1]

def test_natural_top_does_not_capture_approval_commands(monkeypatch):
    assert q.handle("motogp alle")==2
    assert q.handle("motogp 1")==2
