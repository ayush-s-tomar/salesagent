import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.graph as graph  # noqa: E402
import ml.scorer as scorer  # noqa: E402

URL = "https://www.linkedin.com/in/jane-doe/"


def run_research(monkeypatch, news, jobs, tech):
    profile = {"name": "Jane Doe", "title": "CEO", "company": "Acme"}
    tool_log = [
        {"tool": "scrape_linkedin_profile", "args": {}, "result": json.dumps(profile)},
        {"tool": "search_company_news", "args": {}, "result": news},
        {"tool": "analyze_job_postings", "args": {}, "result": jobs},
        {"tool": "find_tech_stack", "args": {}, "result": tech},
    ]
    monkeypatch.setattr(graph, "run_with_tools", lambda prompt, system=None: ("", tool_log))
    return graph.node_research({"linkedin_url": URL, "trace": []})


def test_usable_research_helper():
    assert graph._usable_research("") is None
    assert graph._usable_research(None) is None
    assert graph._usable_research("   ") is None
    assert graph._usable_research("No company name available to search news for.") is None
    assert graph._usable_research("  Could not fetch tech stack: x") is None
    assert graph._usable_research('{"error": "boom"}') is None
    assert graph._usable_research("Acme raised $5M.") == "Acme raised $5M."


def test_failed_searches_are_not_treated_as_research(monkeypatch):
    out = run_research(
        monkeypatch,
        "Could not fetch news: timeout",
        "Could not fetch job postings: boom",
        '{"error": "x"}',
    )
    assert not out.get("company_news")
    assert not out.get("job_postings")
    assert not out.get("tech_stack")


def test_real_results_are_kept(monkeypatch):
    out = run_research(monkeypatch, "Acme raised $5M.", "Acme is hiring.", "Acme uses Python.")
    assert out["company_news"] == "Acme raised $5M."
    assert out["job_postings"] == "Acme is hiring."
    assert out["tech_stack"] == "Acme uses Python."


def test_failed_news_does_not_earn_score_credit(monkeypatch, tmp_path):
    monkeypatch.setattr(scorer, "MODEL_PATH", tmp_path / "model.pkl")
    monkeypatch.setattr(scorer, "SCALER_PATH", tmp_path / "scaler.pkl")
    state = run_research(monkeypatch, "Could not fetch news: timeout", "Acme is hiring engineers.", "Python.")
    out = graph.node_score(state)
    assert "Active company news found" not in out["score_reasons"]
    assert "Currently hiring (growth signal)" in out["score_reasons"]