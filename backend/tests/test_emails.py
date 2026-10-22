import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import api.emails as emails  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)

CONTEXT = (
    "Subject: Azure growth\n\n"
    "Hi Satya, Azure revenue is projected to grow 37% in Q1 FY2026.\n\n"
    "Best,\nSender"
)


def payload(context=CONTEXT):
    return {
        "lead_name": "Satya Nadella",
        "company": "Microsoft",
        "title": "CEO",
        "context": context,
        "tone": "friendly",
    }


@pytest.fixture(autouse=True)
def reset_limiter():
    emails._last_call.clear()
    yield
    emails._last_call.clear()


def test_requires_existing_draft():
    r = client.post("/api/emails/regenerate", json=payload(context=""))
    assert r.status_code == 400


def test_clean_rewrite_is_returned(monkeypatch):
    rewrite = (
        "Subject: Azure growth\n\n"
        "Hi Satya, Azure revenue is projected to grow 37% in Q1 FY2026.\n\n"
        "Cheers,\nSender"
    )
    monkeypatch.setattr(emails, "chat", lambda messages, system=None: rewrite)
    data = client.post("/api/emails/regenerate", json=payload()).json()
    assert data["email"] == rewrite
    assert "note" not in data


def test_ungrounded_rewrite_falls_back_to_original(monkeypatch):
    bad = "Subject: Costs\n\nWe cut costs by 40% for peers."
    monkeypatch.setattr(emails, "chat", lambda messages, system=None: bad)
    data = client.post("/api/emails/regenerate", json=payload()).json()
    assert data["email"] == CONTEXT
    assert "note" in data


def test_second_call_is_rate_limited(monkeypatch):
    monkeypatch.setattr(emails, "chat", lambda messages, system=None: CONTEXT)
    assert client.post("/api/emails/regenerate", json=payload()).status_code == 200
    assert client.post("/api/emails/regenerate", json=payload()).status_code == 429