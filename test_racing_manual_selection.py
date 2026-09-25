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


def test_article7_manual_qm_rewrites_until_real_pass(monkeypatch):
    article7={
        "story_key":"motogp:1091425",
        "title":"Smits replaces Sofouglu at Motoxracing Yamaha, Turkish star joins QJMOTOR in WorldSSP",
        "url":"https://www.worldsbk.com/en/news/2026/09/21/x/1091425",
        "summary":"The Turkish rider will join the Chinese manufacturer in World Supersport while Dutch rider Twan Smits joins the WorldSBK paddock",
        "series":"WorldSBK","source_series":"WorldSBK","series_locked":True,"turkish_rider":"",
    }
    monkeypatch.setattr(rms.agency,"lock_source_series",lambda x,*a,**k:x)
    monkeypatch.setattr(rms.agency,"enrich_turkish",lambda x:(x.update({"turkish_rider":"Bahattin Sofuoglu"}) or x))
    monkeypatch.setattr(rms.agency,"article_info",lambda *a,**k:{})
    calls=[]
    def qualify(x,feedback=None):
        calls.append(feedback)
        if len(calls)==1:
            x["qm_errors"]=["Text nicht an den Fahrer der Quelle gebunden"]
            x["semantic_errors"]=[]
            return False
        x["caption"]="Bahattin Sofuoglu wechselt zu QJMOTOR in die WorldSSP.\n\nFakten aus der Quelle.\n\nWas meint ihr?\n\n#WorldSSP #BahattinSofuoglu #QJMOTOR #Racing"
        x["semantic_qm"]="PASS"; x["racing_qm"]="PASS"
        return True
    monkeypatch.setattr(rms.agency,"qualify_copy",qualify)
    monkeypatch.setattr(rms.agency,"reanalyse_source",lambda x,reasons:x)
    monkeypatch.setattr(rms.agency,"review_batch",lambda items:[(True,[])])
    monkeypatch.setattr(rms.agency,"finish_item",lambda x,i: x.get("semantic_qm")=="PASS" and x.get("racing_qm")=="PASS")
    monkeypatch.setattr(rms.agency,"write_session",lambda *a,**k:None)
    monkeypatch.setattr(rms.agency,"telegram_preview",lambda *a,**k:None)
    monkeypatch.setattr(rms.agency,"is_turkish_focus",lambda x:True)
    assert rms._prepare_one(article7) is True
    assert len(calls)==2
    assert "Text nicht an den Fahrer" in calls[1][0]


def test_article7_stale_worldsbk_lock_is_corrected_from_official_headline():
    article7={
        "story_key":"motogp:1091425",
        "title":"Smits replaces Sofouglu at Motoxracing Yamaha, Turkish star joins QJMOTOR in WorldSSP",
        "url":"https://www.worldsbk.com/en/news/2026/09/21/x/1091425",
        "summary":"The Turkish rider will join the Chinese manufacturer in World Supersport while Dutch rider Twan Smits joins the WorldSBK paddock",
        "series":"WorldSBK","source_series":"WorldSBK","series_locked":True,
    }
    rms.agency.lock_source_series(article7)
    assert article7["series"]=="WorldSSP"
    assert article7["source_series"]=="WorldSSP"
    assert article7["series_origin"]=="explicit-source"
    assert rms.agency.series_for(article7)=="WorldSSP"
    article7["caption"]="Fakten aus der Quelle."
    assert rms.agency.hashtags(article7).split()[0]=="#WorldSSP"


def test_prepare_one_registers_ready_batch_for_telegram_approval(monkeypatch,tmp_path):
    article={
        "story_key":"motogp:1091425",
        "title":"Bahattin Sofuoglu joins QJMOTOR in WorldSSP",
        "url":"https://www.worldsbk.com/en/news/x/1091425",
        "summary":"Bahattin Sofuoglu joins QJMOTOR in WorldSSP",
        "series":"WorldSSP","source_series":"WorldSSP","series_locked":True,
    }
    state=tmp_path/"RACING_RUN_STATE.json"
    monkeypatch.setattr(rms.rc,"STATE",state)
    monkeypatch.setattr(rms.rc,"event_name",lambda:"workflow_dispatch")
    monkeypatch.setattr(rms.rc,"github_run_id",lambda:"article7-e2e")
    monkeypatch.setattr(rms.agency,"lock_source_series",lambda x,*a,**k:x)
    monkeypatch.setattr(rms.agency,"enrich_turkish",lambda x:x)
    monkeypatch.setattr(rms.agency,"article_info",lambda *a,**k:{})
    monkeypatch.setattr(rms.agency,"qualify_copy",lambda x,feedback=None:True)
    monkeypatch.setattr(rms.agency,"review_batch",lambda items:[(True,[])])
    monkeypatch.setattr(rms.agency,"finish_item",lambda x,i:True)
    monkeypatch.setattr(rms.agency,"write_session",lambda *a,**k:None)
    monkeypatch.setattr(rms.agency,"telegram_preview",lambda *a,**k:None)
    monkeypatch.setattr(rms.agency,"is_turkish_focus",lambda x:True)

    assert rms._prepare_one(article) is True
    data=json.loads(state.read_text(encoding="utf-8"))
    bid=data["active_batch_id"]
    assert bid
    assert data["runs"][bid]["status"]=="READY_FOR_APPROVAL"
    assert data["runs"][bid]["origin"]=="manual_racing_selection"
    assert data["runs"][bid]["story_key"]=="motogp:1091425"
