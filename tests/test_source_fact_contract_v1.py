from pathlib import Path
import json

FIXTURE = Path(__file__).parent / "fixtures" / "source_fact_contract_v1.json"


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _fixture(data, story_key):
    return next(x for x in data["fixtures"] if x["story_key"] == story_key)


def test_contract_shape_and_fail_closed_rule():
    data = _load()
    assert data["contract_version"] == "SOURCE-FACT-CONTRACT-V1"
    assert data["source_scope"]["allowed"] == ["series", "title", "summary", "locked_metadata"]
    assert data["source_scope"]["external_knowledge"] is False
    assert data["pass_rule"] == "coverage_complete == true AND every FACT.status == SUPPORTED AND no UNSUPPORTED claims"
    assert len(data["fixtures"]) == 3


def test_valencia_real_pipeline_fixture_is_fail():
    data = _load()
    x = _fixture(data, "motogp:1091638")
    assert x["summary"] == ""
    assert "Valencia GP as 2027 season finale" in x["title"]
    assert x["expected_overall_status"] == "FAIL"
    claims = x["expected_claims"]
    assert any(c["status"] == "SUPPORTED" and "2027 season finale" in c["evidence"] for c in claims)
    assert any(c["status"] == "UNSUPPORTED" and "traditionally" in c["claim"] for c in claims)


def test_bulega_real_pipeline_fixture_is_pass():
    data = _load()
    x = _fixture(data, "motogp:1091502")
    assert x["summary"] == ""
    assert "one of WorldSBK's most impressive records from Bautista" in x["title"]
    assert "record once thought unassailable" in x["title"]
    assert x["expected_overall_status"] == "PASS"
    facts = [c for c in x["expected_claims"] if c["claim_type"] == "FACT"]
    assert facts and all(c["status"] == "SUPPORTED" for c in facts)


def test_worldssp_real_pipeline_fixture_is_pass():
    data = _load()
    x = _fixture(data, "motogp:1091358")
    assert "All three WorldSSP titles on the line at Cremona" in x["title"]
    assert x["summary"] == "With three rounds left to ride, Cremona will be make or break for title hopes of many teams, riders and manufacturers"
    assert x["expected_overall_status"] == "PASS"
    facts = [c for c in x["expected_claims"] if c["claim_type"] == "FACT"]
    assert facts and all(c["status"] == "SUPPORTED" for c in facts)
    questions = [c for c in x["expected_claims"] if c["claim_type"] == "OPINION_QUESTION"]
    assert len(questions) == 1 and questions[0]["status"] == "SUPPORTED"
