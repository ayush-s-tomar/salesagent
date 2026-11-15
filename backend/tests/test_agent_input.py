import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)

VALID = [
    ("https://www.linkedin.com/in/satyanadella/", "https://www.linkedin.com/in/satyanadella/"),
    ("https://linkedin.com/in/satyanadella", "https://linkedin.com/in/satyanadella"),
    ("  http://uk.linkedin.com/in/jane-doe?trk=abc#top  ", "http://uk.linkedin.com/in/jane-doe"),
]

INVALID = [
    None,
    "",
    "   ",
    "not a url",
    "https://example.com/in/someone",
    "https://linkedin.com/company/acme",
    "https://linkedin.com/in/",
    "https://linkedin.com/in/a/b",
    "javascript:alert(1)",
    "https://notlinkedin.com/in/x",
    "https://www.notlinkedin.com/in/x",
    "https://evil.com/?u=https://linkedin.com/in/x",
    "x" * 400,
]


@pytest.fixture(autouse=True)
def reset_limiter():
    main._rate_limit_store.clear()
    yield
    main._rate_limit_store.clear()


@pytest.mark.parametrize("raw,expected", VALID)
def test_valid_urls_are_normalised(raw, expected):
    assert main._normalize_linkedin_url(raw) == expected


@pytest.mark.parametrize("raw", INVALID)
def test_invalid_urls_are_rejected(raw):
    assert main._normalize_linkedin_url(raw) is None


def test_route_rejects_bad_url_without_using_the_rate_limit_slot(monkeypatch):
    called = []

    async def fake_run_agent(**kwargs):
        called.append(kwargs)
        yield {"step": "complete", "status": "done", "msg": "ok", "data": {}}

    monkeypatch.setattr(main, "run_agent", fake_run_agent)

    bad = client.post("/api/agent/run", json={"linkedin_url": "https://example.com/in/x"})
    assert bad.status_code == 400
    assert called == []

    good = client.post("/api/agent/run", json={"linkedin_url": "https://linkedin.com/in/jane-doe?x=1"})
    assert good.status_code == 200
    assert "[DONE]" in good.text
    assert called[0]["linkedin_url"] == "https://linkedin.com/in/jane-doe"


def test_missing_url_is_rejected():
    assert client.post("/api/agent/run", json={}).status_code == 400


def test_message_only_request_is_rejected():
    assert client.post("/api/agent/run", json={"message": "research someone"}).status_code == 400