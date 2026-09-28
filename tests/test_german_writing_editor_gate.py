"""Regression tests for the deterministic German racing writing gate."""
from chief_quality_manager import human_text_review


def _item():
    return {
        "title": "ALCOBA AT THE FRONT: Jeremy Alcoba takes Kawasaki's first WorldSSP pole since 2021 at Cremona",
        "summary": "Jeremy Alcoba takes pole. Can Öncü finishes sixth.",
    }


def test_rider_name_typo_is_blocked():
    caption = "Jeremy Alcoba gewinnt die Superpole in Cremona. Wie seht ihr Alocbas Superpole-Sieg?\n\n#WorldSSP #JeremyAlcoba #BuelentsBikeLife"
    ok, errors = human_text_review("Motorcycle Racing", _item(), caption)
    assert not ok
    assert any("Namens-Tippfehler" in e and "Alocbas" in e for e in errors), errors


def test_correct_rider_name_is_not_blocked():
    caption = "Jeremy Alcoba gewinnt die Superpole in Cremona. Wie seht ihr Alcobas Superpole-Sieg?\n\n#WorldSSP #JeremyAlcoba #BuelentsBikeLife"
    ok, errors = human_text_review("Motorcycle Racing", _item(), caption)
    assert not any("Namens-Tippfehler" in e for e in errors), errors


def test_broken_world_champion_word_order_is_blocked():
    item = {"title": "NEW CHAMPION: Bulega secures 2026 WorldSBK title with second place", "summary": "Bulega is the 2026 WorldSBK champion."}
    caption = "Bulega steht mit Platz zwei plötzlich als Weltmeister 2026 WorldSBK fest. Die Entscheidung fiel in Cremona.\n\n#WorldSBK #NicoloBulega #BuelentsBikeLife"
    ok, errors = human_text_review("Motorcycle Racing", item, caption)
    assert not ok
    assert any("Weltmeister" in e or "Titel-/Serien" in e for e in errors), errors


def test_clean_world_champion_sentence_passes_new_language_checks():
    item = {"title": "NEW CHAMPION: Bulega secures 2026 WorldSBK title with second place", "summary": "Bulega is the 2026 WorldSBK champion."}
    caption = "Mit Platz zwei in Cremona sichert sich Bulega den WorldSBK-Weltmeistertitel 2026. Damit steht der neue Weltmeister fest.\n\n#WorldSBK #NicoloBulega #BuelentsBikeLife"
    ok, errors = human_text_review("Motorcycle Racing", item, caption)
    assert not any("Namens-Tippfehler" in e or "Weltmeister-Formulierung" in e or "Titel-/Serien-Wortstellung" in e for e in errors), errors


def test_run137_vor_dem_renne_is_blocked():
    item={"title":"Fermin Aldeguer Japonya MotoGP Öncesi Ameliyat Oldu","summary":"Aldeguer had surgery before the Japan MotoGP round."}
    caption="Fermin Aldeguer musste kurz vor Japan operiert werden. So kurz vor dem Renne auf den OP-Tisch – wie seht ihr das?\n\n#MotoGP #FerminAldeguer #BuelentsBikeLife"
    ok,errors=human_text_review("Motorcycle Racing",item,caption)
    assert not ok
    assert any("vor dem Renne" in e for e in errors),errors

def test_correct_vor_dem_rennen_is_allowed():
    item={"title":"Fermin Aldeguer Japonya MotoGP Öncesi Ameliyat Oldu","summary":"Aldeguer had surgery before the Japan MotoGP round."}
    caption="Fermin Aldeguer musste kurz vor Japan operiert werden. So kurz vor dem Rennen auf den OP-Tisch – wie seht ihr das?\n\n#MotoGP #FerminAldeguer #BuelentsBikeLife"
    ok,errors=human_text_review("Motorcycle Racing",item,caption)
    assert not any("vor dem Renne" in e for e in errors),errors
