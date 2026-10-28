import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import memory.store as store  # noqa: E402

URL_A = "https://www.linkedin.com/in/a/"
URL_B = "https://www.linkedin.com/in/b/"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test.db"))
    store.init_db()


def lead(url):
    return {
        "name": "Example Person", "title": "CEO", "company": "Example Co", "location": "",
        "linkedin_url": url, "score": 90, "email_draft": "Subject: Hi", "stage": "Lead",
    }


def make(url):
    lead_id = store.save_lead(lead(url))
    deal_id = store.save_deal({"lead_id": lead_id, "title": "Example Person - Example Co", "stage": "Lead", "score": 90})
    return lead_id, deal_id


def test_moving_a_deal_updates_the_lead_stage():
    lead_id, deal_id = make(URL_A)
    store.update_deal_stage(deal_id, "Qualified")
    assert store.get_lead(lead_id)["stage"] == "Qualified"
    assert store.get_all_deals()[0]["stage"] == "Qualified"


def test_other_leads_are_not_affected():
    _, deal_a = make(URL_A)
    lead_b, _ = make(URL_B)
    store.update_deal_stage(deal_a, "Closed Won")
    assert store.get_lead(lead_b)["stage"] == "Lead"


def test_rerunning_the_agent_keeps_the_moved_stage():
    lead_id, deal_id = make(URL_A)
    store.update_deal_stage(deal_id, "Contacted")
    store.save_lead(lead(URL_A))
    assert store.get_lead(lead_id)["stage"] == "Contacted"