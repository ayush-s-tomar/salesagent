import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import agent.llm as llm  # noqa: E402
import agent.tools as tools  # noqa: E402


def test_mcp_email_prompt_forbids_invented_facts(monkeypatch):
    seen = {}

    def fake_chat(messages, system=None):
        seen["prompt"] = messages[0]["content"]
        return "Subject: Hi"

    monkeypatch.setattr(llm, "chat", fake_chat)
    out = tools.generate_outreach_email({"name": "Jane Doe", "title": "CEO", "company": "Acme"}, "Sender", "SenderCo")
    assert out == "Subject: Hi"
    assert "do not invent" in seen["prompt"].lower()