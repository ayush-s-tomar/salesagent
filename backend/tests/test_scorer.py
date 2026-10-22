import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import ml.scorer as scorer  # noqa: E402

EMPTY = {k: 0 for k in scorer.FEATURE_ORDER}
FULL = {"has_company": 1, "has_title": 1, "skills_count": 15, "has_summary": 1, "has_news": 1, "has_jobs": 1}


@pytest.fixture(autouse=True)
def temp_model(tmp_path, monkeypatch):
    monkeypatch.setattr(scorer, "MODEL_PATH", tmp_path / "model.pkl")
    monkeypatch.setattr(scorer, "SCALER_PATH", tmp_path / "scaler.pkl")


def test_scores_stay_between_0_and_100():
    cases = [EMPTY, FULL, {**FULL, "skills_count": 500}, {"has_news": 1}, {"has_jobs": 1}]
    for features in cases:
        score = scorer.score_lead(features)["score"]
        assert 0 <= score <= 100


def test_more_signals_score_higher():
    assert scorer.score_lead(FULL)["score"] > scorer.score_lead(EMPTY)["score"]


def test_same_input_gives_same_score():
    assert scorer.score_lead(FULL)["score"] == scorer.score_lead(FULL)["score"]


def test_reasons_are_ordered_and_capped_at_three():
    reasons = scorer._build_reasons(FULL)
    assert reasons == ["Active company news found", "Currently hiring (growth signal)", "Company identified"]


def test_no_signals_gives_no_reasons():
    assert scorer._build_reasons(EMPTY) == []
    assert scorer._build_reasons({"skills_count": 7}) == ["7 listed skills"]


def test_scoring_failure_returns_neutral_score(monkeypatch):
    def boom():
        raise RuntimeError("model missing")

    monkeypatch.setattr(scorer, "load_model", boom)
    assert scorer.score_lead(FULL) == {"score": 50.0, "reasons": []}