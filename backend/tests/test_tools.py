import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402

import agent.tools as tools  # noqa: E402


def fake_search(text):
    class FakeTavily:
        def search(self, **kwargs):
            return {"results": [{"content": text}] if text else []}

    return FakeTavily()


def fake_groq(payload):
    content = payload if isinstance(payload, str) else json.dumps(payload)
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)))


def run(monkeypatch, search_text, extracted):
    monkeypatch.setattr(tools, "_tavily", lambda: fake_search(search_text))
    monkeypatch.setattr(tools, "_groq", lambda: fake_groq(extracted))
    return tools._search_based_profile("https://www.linkedin.com/in/jane-doe/", "Jane Doe")


def extraction(**over):
    base = {"name": "Jane Doe", "title": "Product Manager", "company": "Acme Corp",
            "location": "Berlin", "summary": "", "skills": []}
    base.update(over)
    return base


def test_company_not_in_search_text_is_dropped(monkeypatch):
    profile = run(monkeypatch, "Jane Doe is a product manager based in Berlin.", extraction())
    assert profile["company"] == ""
    assert profile["name"] == "Jane Doe"
    assert profile["title"] == "Product Manager"


def test_company_in_search_text_is_kept(monkeypatch):
    profile = run(monkeypatch, "Jane Doe, Product Manager at Acme Corp, Berlin.", extraction())
    assert profile["company"] == "Acme Corp"


def test_name_mismatch_discards_whole_extraction(monkeypatch):
    profile = run(
        monkeypatch,
        "Ryan Roslansky is CEO of LinkedIn.",
        extraction(name="Ryan Roslansky", title="CEO", company="LinkedIn"),
    )
    assert profile["name"] == "Jane Doe"
    assert profile["company"] == ""
    assert profile["title"] == "Professional"


def test_slug_without_hyphens_still_matches(monkeypatch):
    monkeypatch.setattr(tools, "_tavily", lambda: fake_search("Sundar Pichai is CEO of Google."))
    monkeypatch.setattr(
        tools, "_groq",
        lambda: fake_groq(extraction(name="Sundar Pichai", title="CEO", company="Google")),
    )
    profile = tools._search_based_profile("https://www.linkedin.com/in/sundarpichai/", "Sundarpichai")
    assert profile["name"] == "Sundar Pichai"
    assert profile["company"] == "Google"


def test_no_search_results_returns_slug_only_profile(monkeypatch):
    profile = run(monkeypatch, "", {})
    assert profile["source"] == "slug_only_no_search_results"
    assert profile["company"] == ""
    assert profile["name"] == "Jane Doe"


def test_non_json_extraction_falls_back_to_slug_name(monkeypatch):
    profile = run(monkeypatch, "Some search text", "not json at all")
    assert profile["name"] == "Jane Doe"
    assert profile["company"] == ""


def test_clean_location_removes_duplicate_country():
    assert tools._clean_location("Mountain View, California, United States, US") == (
        "Mountain View, California, United States"
    )


def test_clean_location_handles_empty():
    assert tools._clean_location("") == ""


@pytest.mark.parametrize("fn", [tools.search_company_news, tools.analyze_job_postings, tools.find_tech_stack])
def test_search_tools_refuse_blank_company(fn):
    assert "No company name" in fn("   ")


def test_unknown_tool_is_reported():
    assert tools.execute_tool("nope", {}) == "Unknown tool: nope"


def test_search_failure_is_returned_as_text_not_raised(monkeypatch):
    class Boom:
        def search(self, **kwargs):
            raise RuntimeError("down")

    monkeypatch.setattr(tools, "_tavily", lambda: Boom())
    assert "Could not fetch news" in tools.search_company_news("Acme")