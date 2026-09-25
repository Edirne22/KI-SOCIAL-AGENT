import json
from pathlib import Path
import racing_manual_selection as rms

def rows():
    return [
        {"story_key":"a","title":"Bahattin Sofuoglu joins WorldSSP","url":"https://www.worldsbk.com/a","summary":"Turkish rider","series":"WorldSSP"},
        {"story_key":"b","title":"Valencia finale","url":"https://www.motogp.com/b","summary":"2027","series":"MotoGP"},
    ]

def test_search_and_display_persists_exact_numbering(monkeypatch,tmp_path):
    monkeypatch.setattr(rms,"_all_rows",rows)
    monkeypatch.setattr(rms,"SELECTION_STATE",tmp_path/"selection.json")
    sent=[]; monkeypatch.setattr(rms,"send_message",sent.append)
    result=rms.handle("racing suche Bahattin")
    assert result==1
    state=json.loads((tmp_path/"selection.json").read_text(encoding="utf-8"))
    assert state["rows"][0]["story_key"]=="a"
    assert "1️⃣" in sent[0]

def test_article_uses_last_displayed_list(monkeypatch,tmp_path):
    p=tmp_path/"selection.json"; p.write_text(json.dumps({"label":"Suche","rows":[rows()[1]]}),encoding="utf-8")
    monkeypatch.setattr(rms,"SELECTION_STATE",p)
    chosen=[]; monkeypatch.setattr(rms,"_prepare_one",lambda x: chosen.append(x) or True)
    monkeypatch.setattr(rms,"send_message",lambda *_:None)
    assert rms.handle("racing artikel 1")==1
    assert chosen[0]["story_key"]=="b"

def test_url_rejects_non_official_source(monkeypatch):
    sent=[]; monkeypatch.setattr(rms,"send_message",sent.append)
    assert rms.handle("racing url https://example.com/news")==0
    assert "offizielle" in sent[0]

def test_official_hosts():
    assert rms._official_url("https://www.motogp.com/en/news/x")
    assert rms._official_url("https://www.worldsbk.com/en/news/x")
    assert not rms._official_url("https://worldsbk.com.example.org/x")
