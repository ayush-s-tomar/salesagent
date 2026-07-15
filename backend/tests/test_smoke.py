"""
Smoke tests — verify the core pieces of SalesAgent import cleanly and behave
sanely. These are NOT full integration tests (no real Groq/Tavily calls);
they exist to catch import-time crashes, broken signatures, and obviously
wrong output ranges before they hit main.

Run locally with:
    cd backend
    pytest tests/ -v
"""
import os
import sys

# Ensure dummy keys exist BEFORE any app modules are imported, since several
# of them read os.getenv(...) at import time (e.g. Groq client construction).
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")
os.environ.setdefault("SENDER_NAME", "Test Sender")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_main_app_imports_and_has_fastapi_instance():
    """main.py should import without crashing and expose a FastAPI app."""
    import main
    assert hasattr(main, "app")
    assert type(main.app).__name__ == "FastAPI"


def test_agent_graph_builds():
    """The LangGraph StateGraph should compile without error."""
    from agent.graph import graph, fresh_state

    assert graph is not None
    # fresh_state should return a dict with all expected keys, all None/empty
    state = fresh_state(linkedin_url="https://www.linkedin.com/in/test-user")
    assert state["linkedin_url"] == "https://www.linkedin.com/in/test-user"
    assert state["trace"] == []
    assert state["profile"] is None


def test_lead_scorer_returns_valid_range():
    """score_lead should always return a number between 0 and 100."""
    from ml.scorer import score_lead

    # A "strong" lead — every signal present
    strong_features = {
        "has_company": 1,
        "has_title": 1,
        "skills_count": 12,
        "has_summary": 1,
        "has_news": 1,
        "has_jobs": 1,
    }
    strong_score = score_lead(strong_features)
    assert 0 <= strong_score <= 100

    # A "weak" lead — nothing present
    weak_features = {
        "has_company": 0,
        "has_title": 0,
        "skills_count": 0,
        "has_summary": 0,
        "has_news": 0,
        "has_jobs": 0,
    }
    weak_score = score_lead(weak_features)
    assert 0 <= weak_score <= 100

    # A fuller profile should score at least as well as an empty one
    assert strong_score >= weak_score


def test_email_validation_catches_placeholders():
    """_validate_email should flag bracketed placeholders and over-length drafts."""
    from agent.graph import _validate_email, MAX_EMAIL_WORDS

    bad_email = "Subject: Hi [Your Name], following up from [Company]."
    violations = bad_email and _validate_email(bad_email)
    assert any("placeholder" in v.lower() for v in violations)

    too_long = "word " * (MAX_EMAIL_WORDS + 10)
    violations = _validate_email(too_long)
    assert any("words" in v.lower() for v in violations)

    clean_email = "Subject: Quick question\n\nHi Satya, saw the Build 2026 news. Worth a chat?\n\nBest,\nTest Sender"
    assert _validate_email(clean_email) == []