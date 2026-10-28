import json
import os
import sys
import threading
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.llm as llm  # noqa: E402

NAMES = ["search_company_news", "analyze_job_postings", "find_tech_stack"]


def tool_call(i, name):
    return SimpleNamespace(id=f"call_{i}", function=SimpleNamespace(name=name, arguments="{}"))


def response(content=None, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return self.responses.pop(0)


def batched_client():
    calls = [tool_call(i, n) for i, n in enumerate(NAMES)]
    return FakeClient([response(tool_calls=calls), response(content="done")])


def test_batched_tool_calls_run_concurrently_and_keep_order(monkeypatch):
    barrier = threading.Barrier(3)

    def fake_execute(name, args):
        barrier.wait(timeout=5)  # only passes if all three run at the same time
        return f"result:{name}"

    monkeypatch.setattr(llm, "_get_client", lambda: batched_client())
    monkeypatch.setattr(llm, "execute_tool", fake_execute)
    text, log = llm.run_with_tools("go")
    assert text == "done"
    assert [e["tool"] for e in log] == NAMES
    assert [e["result"] for e in log] == [f"result:{n}" for n in NAMES]


def test_one_failing_tool_does_not_break_the_others(monkeypatch):
    def fake_execute(name, args):
        if name == "analyze_job_postings":
            raise RuntimeError("boom")
        return f"result:{name}"

    monkeypatch.setattr(llm, "_get_client", lambda: batched_client())
    monkeypatch.setattr(llm, "execute_tool", fake_execute)
    _, log = llm.run_with_tools("go")
    assert log[0]["result"] == "result:search_company_news"
    assert json.loads(log[1]["result"]) == {"error": "boom"}
    assert log[2]["result"] == "result:find_tech_stack"


def test_single_tool_call_still_works(monkeypatch):
    client = FakeClient([response(tool_calls=[tool_call(0, NAMES[0])]), response(content="ok")])
    monkeypatch.setattr(llm, "_get_client", lambda: client)
    monkeypatch.setattr(llm, "execute_tool", lambda name, args: "only")
    text, log = llm.run_with_tools("go")
    assert text == "ok"
    assert log == [{"tool": NAMES[0], "args": {}, "result": "only"}]