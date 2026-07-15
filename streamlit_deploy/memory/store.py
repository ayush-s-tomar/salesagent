import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "salesagent.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        title TEXT,
        company TEXT,
        location TEXT,
        linkedin_url TEXT UNIQUE,
        email TEXT,
        score REAL DEFAULT 0,
        email_draft TEXT,
        stage TEXT DEFAULT 'Lead',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER REFERENCES leads(id),
        title TEXT,
        stage TEXT DEFAULT 'Lead',
        score REAL DEFAULT 0,
        value REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER REFERENCES leads(id),
        type TEXT,
        content TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


def save_lead(data: dict) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads (name, title, company, location, linkedin_url, score, email_draft, stage)
        VALUES (:name, :title, :company, :location, :linkedin_url, :score, :email_draft, :stage)
        ON CONFLICT(linkedin_url) DO UPDATE SET
            name=excluded.name, title=excluded.title, company=excluded.company,
            score=excluded.score, email_draft=excluded.email_draft,
            updated_at=CURRENT_TIMESTAMP
    """, data)
    conn.commit()
    lead_id = c.lastrowid or c.execute("SELECT id FROM leads WHERE linkedin_url=?", (data.get("linkedin_url"),)).fetchone()["id"]
    conn.close()
    return lead_id


def get_lead(lead_id: int) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_all_leads() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_deal(data: dict) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO deals (lead_id, title, stage, score)
        VALUES (:lead_id, :title, :stage, :score)
    """, data)
    conn.commit()
    deal_id = c.lastrowid
    conn.close()
    return deal_id


def get_all_deals() -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT d.*, l.name as lead_name, l.company, l.email
        FROM deals d LEFT JOIN leads l ON d.lead_id = l.id
        ORDER BY d.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_deal_stage(deal_id: int, stage: str):
    conn = get_conn()
    conn.execute("UPDATE deals SET stage=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (stage, deal_id))
    conn.commit()
    conn.close()


def log_interaction(lead_id: int, type_: str, content: str):
    conn = get_conn()
    conn.execute("INSERT INTO interactions (lead_id, type, content) VALUES (?,?,?)", (lead_id, type_, content))
    conn.commit()
    conn.close()


def get_interactions(lead_id: int) -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM interactions WHERE lead_id=? ORDER BY created_at DESC", (lead_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
