import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")

import pytest  # noqa: E402

import evals.judge as judge  # noqa: E402

GOLDEN = Path(__file__).resolve().parent.parent / "evals" / "golden_set.json"

JUDGE_OK = json.dumps({
    "personalization_score": 4, "correctness_score": 4, "structure_score": 4,
    "criteria_results": {"mentions_company": True, "has_specific_hook": True},
    "reasoning": "ok",
})
JUDGE_LOW = json.dumps({
    "personalization_score": 2, "correctness_score": 3, "structure_score": 4,
    "criteria_results": {"mentions_company": False, "has_specific_hook": False},
    "reasoning": "thin",
})


def fake_client(content):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)))


def case(**criteria):
    base = {"min_score": 0, "must_mention_company": True, "must_have_specific_hook": True,
            "max_word_count": 160, "must_not_contain": ["[Your Name]"]}
    base.update(criteria)
    return {"id": "t1", "notes": "", "criteria": base}


def agent(**over):
    base = {"profile": {"name": "A"}, "score": 90, "email": "Subject: Hi\n\nHello from Acme."}
    base.update(over)
    return base


def test_clean_output_passes(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client(JUDGE_OK))
    assert judge.judge_output(agent(), case())["overall_pass"] is True


def test_overlong_email_fails_even_if_judge_is_happy(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client(JUDGE_OK))
    result = judge.judge_output(agent(email=" ".join(["word"] * 300)), case())
    assert result["word_count"] == 300
    assert result["overall_pass"] is False


def test_forbidden_placeholder_fails(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client(JUDGE_OK))
    result = judge.judge_output(agent(email="Subject: Hi\n\nBest,\n[Your Name]"), case())
    assert result["forbidden_found"] == ["[Your Name]"]
    assert result["overall_pass"] is False


def test_score_below_minimum_fails(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client(JUDGE_OK))
    assert judge.judge_output(agent(score=10), case(min_score=60))["overall_pass"] is False


def test_low_signal_case_passes_when_it_expects_no_company(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client(JUDGE_LOW))
    result = judge.judge_output(agent(), case(must_mention_company=False, must_have_specific_hook=False))
    assert result["overall_pass"] is True


def test_empty_judge_response_is_flagged_not_silently_scored(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client("{}"))
    result = judge.judge_output(agent(), case())
    assert result["judge_incomplete"] is True
    assert result["overall_pass"] is False


def test_invalid_json_is_reported(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client("this is not json"))
    result = judge.judge_output(agent(), case())
    assert "JUDGE_PARSE_ERROR" in result["reasoning"]
    assert result["overall_pass"] is False


def test_code_fenced_json_is_parsed(monkeypatch):
    monkeypatch.setattr(judge, "client", fake_client("```json\n" + JUDGE_OK + "\n```"))
    assert judge.judge_output(agent(), case())["overall_pass"] is True


def test_golden_set_is_well_formed():
    cases = json.loads(GOLDEN.read_text())
    assert len(cases) >= 3
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    for c in cases:
        assert c["linkedin_url"].startswith("https://")
        assert "max_word_count" in c["criteria"]