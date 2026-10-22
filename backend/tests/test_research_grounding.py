import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.graph as graph  # noqa: E402

URL = "https://www.linkedin.com/in/random-startup-founder-xyz/"


def run_research(monkeypatch, profile):
    tool_log = [
        {"tool": "scrape_linkedin_profile", "args": {}, "result": json.dumps(profile)},
        {"tool": "search_company_news", "args": {"company_name": "Ritten"}, "result": "Ritten raised $35M."},
        {"tool": "analyze_job_postings", "args": {"company_name": "Ritten"}, "result": "Hiring engineers."},
        {"tool": "find_tech_stack", "args": {"company_name": "Ritten"}, "result": "Python."},
    ]
    monkeypatch.setattr(graph, "run_with_tools", lambda prompt, system=None: ("", tool_log))
    return graph.node_research({"linkedin_url": URL, "trace": []})


def test_research_for_unknown_company_is_discarded(monkeypatch):
    profile = {"name": "Random Startup Founder Xyz", "title": "Professional", "company": ""}
    out = run_research(monkeypatch, profile)
    assert not out.get("company_news")
    assert not out.get("job_postings")
    assert not out.get("tech_stack")
    assert out["profile"]["name_from_url"] is True


def test_research_for_known_company_is_kept(monkeypatch):
    profile = {"name": "Jane Doe", "title": "CEO", "company": "Acme"}
    out = run_research(monkeypatch, profile)
    assert out["company_news"] == "Ritten raised $35M."
    assert not out["profile"].get("name_from_url")


def test_unknown_name_and_no_research_gives_neutral_fallback_email():
    state = {
        "profile": {"name": "Random Startup Founder Xyz", "title": "Professional", "company": "", "name_from_url": True},
        "company_news": None, "job_postings": None, "tech_stack": None, "trace": [],
    }
    out = graph.node_email(state)
    assert "Hi there," in out["email_draft"]
    assert "Xyz" not in out["email_draft"]