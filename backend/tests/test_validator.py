import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.graph import _validate_email, _fallback_email  # noqa: E402

SOURCE = "Azure revenue is projected to grow 37% in Q1 FY2026. Microsoft announced a policy on Jan 26 2026."


def test_clean_email_passes():
    email = "Subject: Azure growth\n\nHi Satya, Azure revenue is projected to grow 37% in Q1 FY2026."
    assert _validate_email(email, SOURCE) == []


def test_refusal_is_rejected():
    violations = _validate_email("I'm unable to craft this email.", SOURCE)
    assert any("refusal" in v for v in violations)


def test_invented_number_is_rejected():
    violations = _validate_email("We cut integration time by 40% for peers.", SOURCE)
    assert any("'40'" in v for v in violations)


def test_invented_date_is_rejected():
    violations = _validate_email("On Mar 5 2026 your team changed course.", SOURCE)
    assert any("date not found" in v for v in violations)


def test_filler_phrase_is_rejected():
    violations = _validate_email("I noticed that Azure is growing.", SOURCE)
    assert any("filler" in v for v in violations)


def test_placeholder_is_rejected():
    violations = _validate_email("Best,\n[Your Name]", SOURCE)
    assert any("placeholder" in v for v in violations)


def test_overlong_email_is_rejected():
    violations = _validate_email(" ".join(["word"] * 200), SOURCE)
    assert any("words" in v for v in violations)


def test_fallback_email_is_never_blank():
    email = _fallback_email("there", "", "", "Sender")
    assert email.startswith("Subject:")
    assert "Hi there," in email
    assert "Sender" in email