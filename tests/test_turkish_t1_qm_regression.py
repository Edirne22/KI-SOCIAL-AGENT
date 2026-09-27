import types
import turkish_editor_qm as tq

SOURCE_URL="https://tr.motorsport.com/supersport/news/wssp-cremona-2-yaris-alcobadan-ust-uste-ikinci-zafer-can-oncu-11-bahattin-sofuoglu-21-sirada/10859593"

def test_editorial_text_excludes_provenance_url():
    cap="Jeremy Alcoba feiert in Cremona seinen zweiten Sieg in Folge. Can Öncü wird Elfter.\n\n#WorldSSP #CanOncu\n\nQuelle / weitere Infos: "+SOURCE_URL
    assert tq._editorial_text(cap)=="Jeremy Alcoba feiert in Cremona seinen zweiten Sieg in Folge. Can Öncü wird Elfter."

def test_t1_url_id_is_not_a_source_fact_number():
    # Regression for Telegram T1 on 2026-09-27: 10859593 is an article id,
    # not a racing fact and therefore must never be required in source facts.
    item={"title":"WSSP Cremona 2. yarış: Alcoba’dan üst üste ikinci zafer, Can Öncü 11., Bahattin Sofuoğlu 21. sırada",
          "summary":"Jeremy Alcoba won the second WorldSSP race at Cremona. Can Öncü finished 11th and Bahattin Sofuoğlu 21st.",
          "url":SOURCE_URL,"turkish_rider":"Can Öncü","series":"WorldSSP"}
    source=tq._source_text(item)
    assert "10859593" not in source
    assert "11" in source and "21" in source

def test_unverified_nationality_still_fails_closed():
    item={"title":"Can Öncü Cremona WorldSSP","summary":"Can Öncü finished 11th.","series":"WorldSSP"}
    from racing_final_guard import review
    ok,errors=review(item,"Der Türke Can Öncü wurde Elfter. #WorldSSP")
    assert not ok
    assert any("Nationalitaet" in e for e in errors)

if __name__=="__main__":
    test_editorial_text_excludes_provenance_url();test_t1_url_id_is_not_a_source_fact_number();test_unverified_nationality_still_fails_closed();print("TURKISH T1 QM REGRESSION: PASS")
