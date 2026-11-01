import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.tools as tools  # noqa: E402


def test_compound_company_is_reduced_to_the_grounded_part():
    text = "Sundar Pichai is CEO of Google."
    assert tools._ground_company("Google / Alphabet", text, "Sundarpichai") == "Google"


def test_full_name_in_text_is_kept_as_is():
    assert tools._ground_company("Acme Corp", "Jane Doe at Acme Corp", "Jane Doe") == "Acme Corp"


def test_ungrounded_company_is_dropped():
    assert tools._ground_company("Acme Corp", "Jane Doe is a manager", "Jane Doe") == ""


def test_company_made_of_slug_words_is_dropped():
    text = "Random Startup Founder Xyz - XYZ"
    assert tools._ground_company("XYZ", text, "Random Startup Founder Xyz") == ""


def test_slug_part_is_skipped_but_a_real_part_is_kept():
    text = "Founder at Acme"
    assert tools._ground_company("XYZ / Acme", text, "Random Founder Xyz") == "Acme"


def test_profile_with_compound_company_keeps_the_grounded_part(monkeypatch):
    class FakeTavily:
        def search(self, **kwargs):
            return {"results": [{"content": "Sundar Pichai - CEO - Google"}]}

    payload = {"name": "Sundar Pichai", "title": "CEO", "company": "Google / Alphabet",
               "location": "", "summary": "", "skills": []}
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )
    groq = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)))
    monkeypatch.setattr(tools, "_tavily", lambda: FakeTavily())
    monkeypatch.setattr(tools, "_groq", lambda: groq)
    profile = tools._search_based_profile("https://www.linkedin.com/in/sundarpichai/", "Sundarpichai")
    assert profile["company"] == "Google"