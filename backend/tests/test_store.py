import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import memory.store as store  # noqa: E402


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test.db"))
    store.init_db()


def lead(url="https://www.linkedin.com/in/example/"):
    return {
        "name": "Example Person",
        "title": "CEO",
        "company": "Example Co",
        "location": "",
        "linkedin_url": url,
        "score": 90,
        "email_draft": "Subject: Hi",
        "stage": "Lead",
    }


def deal(lead_id, score=90):
    return {"lead_id": lead_id, "title": "Example Person - Example Co", "stage": "Lead", "score": score}


def test_same_lead_twice_gives_one_lead_and_one_deal():
    first = store.save_lead(lead())
    second = store.save_lead(lead())
    assert first == second
    d1 = store.save_deal(deal(first))
    d2 = store.save_deal(deal(second))
    assert d1 == d2
    assert len(store.get_all_leads()) == 1
    assert len(store.get_all_deals()) == 1


def test_rerun_keeps_the_moved_stage_but_refreshes_score():
    lead_id = store.save_lead(lead())
    deal_id = store.save_deal(deal(lead_id, score=50))
    store.update_deal_stage(deal_id, "Contacted")
    store.save_deal(deal(lead_id, score=95))
    deals = store.get_all_deals()
    assert len(deals) == 1
    assert deals[0]["stage"] == "Contacted"
    assert deals[0]["score"] == 95


def test_different_leads_get_separate_deals():
    a = store.save_lead(lead("https://www.linkedin.com/in/a/"))
    b = store.save_lead(lead("https://www.linkedin.com/in/b/"))
    store.save_deal(deal(a))
    store.save_deal(deal(b))
    assert len(store.get_all_deals()) == 2