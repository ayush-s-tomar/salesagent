import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.tools as tools  # noqa: E402


def stub(monkeypatch, search_text, extracted):
    class FakeTavily:
        def search(self, **kwargs):
            return {"results": [{"content": search_text}]}

    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(extracted)))]
    )
    groq = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)))
    monkeypatch.setattr(tools, "_tavily", lambda: FakeTavily())
    monkeypatch.setattr(tools, "_groq", lambda: groq)


def test_company_copied_from_url_slug_is_dropped(monkeypatch):
    stub(
        monkeypatch,
        "Random Startup Founder Xyz - Owner - XYZ",
        {"name": "Random Startup Founder Xyz", "title": "Owner", "company": "XYZ",
         "location": "", "summary": "", "skills": []},
    )
    profile = tools._search_based_profile(
        "https://www.linkedin.com/in/random-startup-founder-xyz/", "Random Startup Founder Xyz"
    )
    assert profile["company"] == ""


def test_real_company_not_in_slug_is_kept(monkeypatch):
    stub(
        monkeypatch,
        "Jane Doe, CEO at Acme Corp",
        {"name": "Jane Doe", "title": "CEO", "company": "Acme Corp",
         "location": "", "summary": "", "skills": []},
    )
    profile = tools._search_based_profile("https://www.linkedin.com/in/jane-doe/", "Jane Doe")
    assert profile["company"] == "Acme Corp"