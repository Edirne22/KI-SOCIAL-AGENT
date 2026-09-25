from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import racing_semantic_qm as semantic

FIXTURE = Path(__file__).parent / "fixtures" / "source_fact_contract_v1.json"


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _fixture(data, story_key):
    return next(x for x in data["fixtures"] if x["story_key"] == story_key)


def _model_response(x):
    claims = []
    for c in x["expected_claims"]:
        evidence = []
        if c["evidence_field"] != "NONE":
            evidence = [{"source_field": c["evidence_field"], "quote": c["evidence"]}]
        claims.append({
            "claim": c["claim"],
            "claim_type": c["claim_type"],
            "status": c["status"],
            "source_evidence": evidence,
        })
    return {
        "contract_version": "SOURCE-FACT-CONTRACT-V1",
        "coverage_complete": True,
        "claims": claims,
        "german_ok": True,
        "style_ok": True,
        "repair_reasons": [],
    }


def _run_real_fixture(x):
    old = semantic.generate
    try:
        semantic.generate = lambda task, prompt: json.dumps(_model_response(x), ensure_ascii=False)
        item = {"series": x["series"], "title": x["title"], "summary": x["summary"]}
        return semantic.review_detailed(item, x["caption_under_test"])
    finally:
        semantic.generate = old


def test_contract_shape_and_fail_closed_rule():
    data = _load()
    assert data["contract_version"] == "SOURCE-FACT-CONTRACT-V1"
    assert data["source_scope"]["allowed"] == ["series", "title", "summary", "locked_metadata"]
    assert data["source_scope"]["external_knowledge"] is False
    assert data["pass_rule"] == "coverage_complete == true AND every FACT.status == SUPPORTED AND no UNSUPPORTED claims"
    assert len(data["fixtures"]) == 3
    assert "or (not hard_reasons)" not in (ROOT / "racing_semantic_qm.py").read_text(encoding="utf-8")


def test_valencia_real_pipeline_fixture_is_fail():
    data = _load()
    x = _fixture(data, "motogp:1091638")
    assert x["summary"] == ""
    assert x["expected_overall_status"] == "FAIL"
    result = _run_real_fixture(x)
    assert result["coverage_complete"] is True
    assert result["hard_ok"] is False
    assert any("traditionally" in reason for reason in result["hard_reasons"])


def test_bulega_real_pipeline_fixture_is_fail_closed_on_added_specificity():
    data = _load()
    x = _fixture(data, "motogp:1091502")
    assert x["summary"] == ""
    assert "one of WorldSBK's most impressive records from Bautista" in x["title"]
    assert "record once thought unassailable" in x["title"]
    assert x["expected_overall_status"] == "FAIL"
    result = _run_real_fixture(x)
    assert result["hard_ok"] is False
    assert any("riders' championship specifically" in reason for reason in result["hard_reasons"])
    assert any("for a long time" in reason for reason in result["hard_reasons"])


def test_worldssp_real_pipeline_fixture_is_pass():
    data = _load()
    x = _fixture(data, "motogp:1091358")
    assert x["expected_overall_status"] == "PASS"
    result = _run_real_fixture(x)
    assert result["hard_ok"] is True
    assert result["language_ok"] is True
    assert result["hard_reasons"] == []


def test_contract_rejects_missing_coverage_and_fake_evidence():
    x = _fixture(_load(), "motogp:1091358")
    item = {"series": x["series"], "title": x["title"], "summary": x["summary"]}
    bad = _model_response(x)
    bad["coverage_complete"] = False
    try:
        semantic._validate_contract(item, bad)
        raise AssertionError("coverage_complete=false must fail closed")
    except ValueError:
        pass
    bad = _model_response(x)
    bad["claims"][0]["source_evidence"][0]["quote"] = "invented evidence not present in source"
    try:
        semantic._validate_contract(item, bad)
        raise AssertionError("invented evidence quote must fail closed")
    except ValueError:
        pass


def main():
    test_contract_shape_and_fail_closed_rule()
    test_valencia_real_pipeline_fixture_is_fail()
    test_bulega_real_pipeline_fixture_is_fail_closed_on_added_specificity()
    test_worldssp_real_pipeline_fixture_is_pass()
    test_contract_rejects_missing_coverage_and_fake_evidence()
    print("SOURCE-FACT-CONTRACT-V1 PRODUCTION SEMANTIC-QM: PASS")


if __name__ == "__main__":
    main()
