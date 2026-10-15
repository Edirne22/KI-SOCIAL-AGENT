"""Offline language contracts. These tests do not certify live translation quality."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
import translation_router as tr
import turkish_editor_qm as editor

@pytest.mark.parametrize("text",["", "  ", None, [], 42])
def test_empty_translation_input_never_calls_provider(monkeypatch,text):
    request=Mock()
    monkeypatch.setattr(tr.requests,"post",request)
    with pytest.raises(ValueError):
        tr.TranslationRouter().translate(text,"de","tr")
    request.assert_not_called()

@pytest.mark.parametrize("answer",["", "  ", None, [], {"text":"wrong envelope"}])
def test_unusable_fallback_is_not_success(monkeypatch,answer):
    monkeypatch.delenv("NVIDIA_API_KEY",raising=False)
    monkeypatch.setattr(tr.llm_router,"quick_chat",lambda *a,**k:answer)
    with pytest.raises(RuntimeError):
        tr.TranslationRouter().translate("Hallo","de","tr")

@pytest.mark.parametrize("answer",['null','[]','{"caption":null}','{"caption":42}',
                                    '{"caption":{}}','{"caption":" "}',None])
def test_editor_invalid_content_never_becomes_a_caption(monkeypatch,answer):
    agency=SimpleNamespace(series_for=lambda x:"MotoGP")
    item={"turkish_rider":"Toprak Razgatlıoğlu","title":"Source"}
    monkeypatch.setattr(editor,"quick_chat",lambda *a,**k:answer)
    assert editor.edit(item,agency)==""
    assert "caption" not in item

def test_provider_failure_uses_existing_failure_path(monkeypatch):
    agency=SimpleNamespace(series_for=lambda x:"MotoGP")
    def unavailable(*a,**k):raise RuntimeError("synthetic outage")
    monkeypatch.setattr(editor,"quick_chat",unavailable)
    assert editor.edit({"turkish_rider":"Toprak Razgatlıoğlu"},agency)==""

def test_real_editor_prompt_preserves_voice_and_source_contract(monkeypatch):
    agency=SimpleNamespace(series_for=lambda x:"MotoGP")
    item={"turkish_rider":"Toprak Razgatlıoğlu","title":"Source","summary":"Source facts"}
    chat=Mock(return_value='{"caption":"Toprak Razgatlıoğlu blieb ohne Punkte."}')
    monkeypatch.setattr(editor,"quick_chat",chat)
    result=editor.edit(item,agency)
    prompt=chat.call_args.args[0]
    assert "Schreibe auf Deutsch" in prompt
    assert "Schreibe wie Buelent selbst" in prompt
    assert "Keine erfundenen persoenlichen Erlebnisse" in prompt
    assert "Nur Fakten aus TITEL/ZUSAMMENFASSUNG" in prompt
    assert "Toprak Razgatlıoğlu blieb ohne Punkte." in result
