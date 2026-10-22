import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402

import agent.llm as llm  # noqa: E402


class FakeRateLimit(Exception):
    pass


@pytest.fixture(autouse=True)
def fake_rate_limit_class(monkeypatch):
    monkeypatch.setattr(llm, "RateLimitError", FakeRateLimit)


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.last_kwargs = {}
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_wait_time_plain_seconds():
    err = FakeRateLimit("Rate limit reached. Please try again in 8.865s.")
    assert llm._seconds_from_rate_limit_error(err) == pytest.approx(9.365)


def test_wait_time_minutes_and_seconds():
    err = FakeRateLimit("Rate limit reached. Please try again in 10m23.376s.")
    assert llm._seconds_from_rate_limit_error(err) == pytest.approx(623.876)


def test_wait_time_falls_back_when_unparseable():
    assert llm._seconds_from_rate_limit_error(FakeRateLimit("something odd")) == 5.0


def test_daily_quota_detected():
    err = FakeRateLimit("Rate limit reached on tokens per day (TPD): Limit 200000")
    assert llm._is_daily_quota_error(err) is True


def test_per_minute_limit_not_treated_as_daily():
    err = FakeRateLimit("Rate limit reached on tokens per minute (TPM): Limit 8000")
    assert llm._is_daily_quota_error(err) is False


def test_daily_quota_fails_fast_without_sleeping(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", lambda s: sleeps.append(s))
    client = FakeClient([FakeRateLimit("tokens per day (TPD) reached. Please try again in 10m0s.")])
    with pytest.raises(llm.DailyQuotaExceededError) as exc:
        llm._create_with_retry(client, model="m", messages=[])
    assert client.calls == 1
    assert sleeps == []
    assert exc.value.wait_seconds == pytest.approx(600.5)


def test_per_minute_limit_retries_then_succeeds(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", lambda s: sleeps.append(s))
    client = FakeClient([FakeRateLimit("tokens per minute (TPM). Please try again in 2s."), "ok"])
    assert llm._create_with_retry(client, model="m", messages=[]) == "ok"
    assert client.calls == 2
    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(2.5)


def test_per_minute_limit_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    errors = [FakeRateLimit("TPM limit. Please try again in 1s.") for _ in range(llm.MAX_RETRIES)]
    client = FakeClient(errors)
    with pytest.raises(FakeRateLimit):
        llm._create_with_retry(client, model="m", messages=[])
    assert client.calls == llm.MAX_RETRIES


def test_chat_returns_empty_string_for_empty_content_and_uses_low_effort(monkeypatch):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))])
    client = FakeClient([response])
    monkeypatch.setattr(llm, "_get_client", lambda: client)
    assert llm.chat([{"role": "user", "content": "hi"}]) == ""
    assert client.last_kwargs["extra_body"] == {"reasoning_effort": "low"}