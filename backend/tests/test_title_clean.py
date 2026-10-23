import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

from agent.tools import _clean_title  # noqa: E402

SLUG_NAME = "Random Startup Founder Xyz"


def test_slug_word_segment_is_removed():
    assert _clean_title("Owner, XYZ", SLUG_NAME) == "Owner"


def test_title_that_is_only_slug_words_becomes_empty():
    assert _clean_title("Xyz", SLUG_NAME) == ""


def test_real_title_is_unchanged():
    assert _clean_title("Chairman and CEO", "Satya Nadella") == "Chairman and CEO"


def test_title_with_separator_but_no_slug_words_is_unchanged():
    assert _clean_title("Product Manager | Acme", "Jane Doe") == "Product Manager | Acme"


def test_empty_title_is_safe():
    assert _clean_title("", SLUG_NAME) == ""
    assert _clean_title("   ", SLUG_NAME) == ""