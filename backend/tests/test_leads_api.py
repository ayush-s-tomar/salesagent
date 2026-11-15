import csv
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")
os.environ.setdefault("TAVILY_API_KEY", "test-dummy-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import memory.store as store  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test.db"))
    store.init_db()


def make_lead(name="Example Person", url="https://www.linkedin.com/in/example/"):
    return store.save_lead({
        "name": name, "title": "CEO", "company": "Example Co", "location": "",
        "linkedin_url": url, "score": 90, "email_draft": "Subject: Hi", "stage": "Lead",
    })


def rows(response):
    return list(csv.reader(io.StringIO(response.text)))


def test_export_returns_csv_with_header_and_rows():
    make_lead()
    r = client.get("/api/leads/export.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    table = rows(r)
    assert table[0][:3] == ["id", "name", "title"]
    assert table[1][1] == "Example Person"


def test_export_with_no_leads_is_header_only():
    assert len(rows(client.get("/api/leads/export.csv"))) == 1


def test_formula_like_cells_are_neutralised():
    make_lead(name="=1+1")
    table = rows(client.get("/api/leads/export.csv"))
    assert table[1][1] == "'=1+1"


def test_patch_saves_edited_email_draft_and_logs_it():
    lead_id = make_lead()
    r = client.patch(f"/api/leads/{lead_id}", json={"email_draft": "Subject: New\n\nHello"})
    assert r.status_code == 200
    detail = client.get(f"/api/leads/{lead_id}").json()
    assert detail["email_draft"] == "Subject: New\n\nHello"
    assert [i["type"] for i in detail["interactions"]] == ["email_edited"]


def test_patch_rejects_oversized_draft():
    lead_id = make_lead()
    r = client.patch(f"/api/leads/{lead_id}", json={"email_draft": "x" * 6000})
    assert r.status_code == 400


def test_patch_rejects_blank_draft():
    lead_id = make_lead()
    r = client.patch(f"/api/leads/{lead_id}", json={"email_draft": "   "})
    assert r.status_code == 400


def test_patch_unknown_lead_is_404():
    assert client.patch("/api/leads/999", json={"email_draft": "x"}).status_code == 404