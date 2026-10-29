import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.tools as tools  # noqa: E402

URL = "https://www.linkedin.com/in/jane-doe/"

WRONG = (
    "D Meier, Other Co",
    {"name": "D Meier", "title": "Manager", "company": "Other Co", "location": "", "summary": "", "skills": []},
)
RIGHT = (
    "Jane Doe, CEO at Acme Corp",
    {"name": "Jane Doe", "title": "CEO", "company": "Acme Corp", "location": "", "summary": "", "skills": []},
)


def stub(monkeypatch, attempts):
    texts = [a[0] for a in attempts]
    payloads = [a[1] for a in attempts]
    queries = []

    class FakeTavily:
        def search(self, **kwargs):
            queries.append(kwargs.get("query"))
            return {"results": [{"content": texts[len(queries) - 1]}]}

    def create(**kwargs):
        content = json.dumps(payloads[len(queries) - 1])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    groq = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(tools, "_tavily", lambda: FakeTavily())
    monkeypatch.setattr(tools, "_groq", lambda: groq)
    return queries


def test_wrong_person_first_then_right_person_on_retry(monkeypatch):
    queries = stub(monkeypatch, [WRONG, RIGHT])
    profile = tools._search_based_profile(URL, "Jane Doe")
    assert len(queries) == 2
    assert queries[0] != queries[1]
    assert profile["name"] == "Jane Doe"
    assert profile["company"] == "Acme Corp"


def test_no_retry_when_first_search_matches(monkeypatch):
    queries = stub(monkeypatch, [RIGHT, WRONG])
    profile = tools._search_based_profile(URL, "Jane Doe")
    assert len(queries) == 1
    assert profile["company"] == "Acme Corp"


def test_both_attempts_wrong_never_accepts_a_stranger(monkeypatch):
    queries = stub(monkeypatch, [WRONG, WRONG])
    profile = tools._search_based_profile(URL, "Jane Doe")
    assert len(queries) == 2
    assert profile["name"] == "Jane Doe"
    assert profile["company"] == ""
    assert profile["title"] == "Professional"