import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402

import agent.graph as graph  # noqa: E402
import ml.scorer as scorer  # noqa: E402


@pytest.fixture(autouse=True)
def temp_model(tmp_path, monkeypatch):
    monkeypatch.setattr(scorer, "MODEL_PATH", tmp_path / "model.pkl")
    monkeypatch.setattr(scorer, "SCALER_PATH", tmp_path / "scaler.pkl")


def score(title):
    state = {"profile": {"name": "A B", "title": title, "company": ""}, "trace": []}
    return graph.node_score(state)


def test_placeholder_title_is_not_credited():
    assert "Job title identified" not in score("Professional")["score_reasons"]


def test_real_title_is_credited():
    assert "Job title identified" in score("Chairman and CEO")["score_reasons"]


def test_missing_title_is_not_credited():
    assert "Job title identified" not in score("")["score_reasons"]