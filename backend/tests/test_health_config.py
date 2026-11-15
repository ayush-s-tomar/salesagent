import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def test_health_reports_configuration_without_leaking_values(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "super-secret-groq-value")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["groq_configured"] is True
    assert body["tavily_configured"] is False
    assert "super-secret-groq-value" not in r.text


def test_health_with_both_keys_set(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "a")
    monkeypatch.setenv("TAVILY_API_KEY", "b")
    body = client.get("/api/health").json()
    assert body["groq_configured"] is True
    assert body["tavily_configured"] is True


def test_health_with_no_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["groq_configured"] is False
    assert body["tavily_configured"] is False