"""Regression test for the V8.5.5 hardening editor-prompt signature."""
import json
import motogp_content_agency_v2 as agency
from racing_v855_hardening import install


VARIANTS = tuple(agency.STRUCTURE_VARIANTS)


def _response_for(variant):
    if variant == "HOOK_BODY_QUESTION":
        return json.dumps({"hook": "Start.", "body": "Fakten bleiben belegt.", "question": "Was meint ihr?"})
    if variant == "BODY_QUESTION":
        return json.dumps({"body": "Fakten bleiben belegt.", "question": "Was meint ihr?"})
    if variant == "STORY_QUESTION":
        return json.dumps({"story": "Die belegte Racing-Story bleibt kompakt.", "question": "Was meint ihr?"})
    if variant == "FACT_FACT_FACT":
        return json.dumps({"facts": ["Fakt eins.", "Fakt zwei.", "Fakt drei."], "cta": "Eure Meinung dazu."})
    if variant == "QUESTION_HOOK_BODY":
        return json.dumps({"question": "Was meint ihr?", "body": "Fakten bleiben belegt."})
    if variant == "ZITAT_BODY":
        return json.dumps({"quote": "Belegte Aussage", "body": "Fakten bleiben belegt.", "question": "Was meint ihr?"})
    raise AssertionError(variant)


def _item():
    return {
        "title": "MotoGP rider returns for the current race weekend",
        "summary": "MotoGP rider returns for the race weekend.",
        "series": "MotoGP",
        "source_series": "MotoGP",
    }


def _run_editor(monkeypatch, variant, reasons):
    monkeypatch.setattr(agency, "choose_structure_variant", lambda: variant)
    monkeypatch.setattr(agency, "generate", lambda task, prompt: _response_for(variant))
    result = agency.german_editor(_item(), reasons)
    assert result
    return result


def test_hardening_wrapper_supports_all_structure_variants(monkeypatch):
    install(agency)
    for variant in VARIANTS:
        assert _run_editor(monkeypatch, variant, None)


def test_hardening_wrapper_forwards_repair_reasons(monkeypatch):
    install(agency)
    for variant in VARIANTS:
        assert _run_editor(monkeypatch, variant, ["Racing-QM: Test-Rueckgabe"])


def test_hardening_wrapper_accepts_none_values(monkeypatch):
    install(agency)
    item = _item()
    assert agency._editor_prompt(item, None, None)
