import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import agent.graph as graph  # noqa: E402
import memory.store as store  # noqa: E402
from main import app  # noqa: E402

URL = "https://www.linkedin.com/in/example/"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test.db"))
    store.init_db()


def make_deal(follow_up=None):
    lead_id = store.save_lead({
        "name": "Example Person", "title": "CEO", "company": "Example Co", "location": "",
        "linkedin_url": URL, "score": 90, "email_draft": "Subject: Hi", "stage": "Lead",
    })
    data = {"lead_id": lead_id, "title": "Example Person - Example Co", "stage": "Lead", "score": 90}
    if follow_up is not None:
        data["follow_up_date"] = follow_up
    return lead_id, store.save_deal(data)


def test_fresh_database_has_the_column():
    columns = [r["name"] for r in store.get_conn().execute("PRAGMA table_info(deals)").fetchall()]
    assert "follow_up_date" in columns


def test_old_database_is_migrated_without_losing_rows(tmp_path, monkeypatch):
    path = str(tmp_path / "old.db")
    old = sqlite3.connect(path)
    old.executescript(
        "CREATE TABLE deals (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER, title TEXT, "
        "stage TEXT DEFAULT 'Lead', score REAL DEFAULT 0, value REAL DEFAULT 0, "
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);"
        "INSERT INTO deals (lead_id, title) VALUES (1, 'Old deal');"
    )
    old.commit()
    old.close()
    monkeypatch.setattr(store, "DB_PATH", path)
    store.init_db()
    store.init_db()  # running it twice must be safe
    rows = store.get_conn().execute("SELECT title, follow_up_date FROM deals").fetchall()
    assert [(r["title"], r["follow_up_date"]) for r in rows] == [("Old deal", None)]


def test_save_deal_stores_the_follow_up_date():
    make_deal("2026-10-29")
    assert store.get_all_deals()[0]["follow_up_date"] == "2026-10-29"


def test_rerun_updates_the_date():
    make_deal("2026-10-29")
    make_deal("2026-11-05")
    deals = store.get_all_deals()
    assert len(deals) == 1
    assert deals[0]["follow_up_date"] == "2026-11-05"


def test_a_save_without_a_date_keeps_the_existing_one():
    make_deal("2026-10-29")
    make_deal()
    assert store.get_all_deals()[0]["follow_up_date"] == "2026-10-29"


def test_deals_api_returns_the_date():
    make_deal("2026-10-29")
    body = TestClient(app).get("/api/deals/").json()
    assert body[0]["follow_up_date"] == "2026-10-29"


def test_node_save_persists_the_date_it_reports():
    state = {
        "profile": {"name": "Example Person", "title": "CEO", "company": "Example Co", "linkedin_url": URL},
        "lead_score": 50,
        "email_draft": "Subject: Hi",
        "trace": [],
    }
    out = graph.node_save(state)
    assert out["followup_date"]
    assert store.get_all_deals()[0]["follow_up_date"] == out["followup_date"]