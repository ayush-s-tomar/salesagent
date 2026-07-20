# SalesAgent — Autonomous B2B Sales AI
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)
![React](https://img.shields.io/badge/frontend-React-61DAFB)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![CI](https://github.com/ayush-s-tomar/salesagent/actions/workflows/ci.yml/badge.svg)

> An AI agent that researches a lead, scores them, and writes a personalized cold email — in 45 seconds, from just a LinkedIn URL.

[🔗 Live Demo (frontend)](https://salesagent-ai.streamlit.app/) &nbsp;|&nbsp; [⚙️ API Docs (backend)](https://salesagent-ufu7.onrender.com/docs) &nbsp;|&nbsp; [📝 Technical Writeup](https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h) &nbsp;|&nbsp; [👤 LinkedIn](https://www.linkedin.com/in/ayush-s-tomar/)

<p align="center">
  <img src="docs/demo-screenshot.png" alt="SalesAgent — one URL in, a scored, personalized lead out" width="800">
</p>

<p align="center">
  <em>One URL in. A scored, personalized lead out — in ~45 seconds.</em>
</p>

<p align="center">
  <img src="docs/demo.gif" alt="SalesAgent — live agent trace walkthrough" width="800">
</p>

<p align="center">
  <em>Live agent trace — research → score → draft → save, end to end.</em>
</p>

### 🎥 Demo Video

https://github.com/user-attachments/assets/2c5d825a-f060-4cbf-9dd5-97f622ee385f

---

## Why I Built This

I was spending 1–2 hours per lead doing manual research before writing a single cold email — checking LinkedIn, Googling company news, digging through job postings for pain points. It felt like exactly the kind of multi-step, tool-using task an LLM agent should own end-to-end, not just assist with. So I built one that does the whole loop: research → score → draft → save → remember.

## The Problem

Manual B2B lead research takes 1–2 hours per lead: checking LinkedIn, Googling company news, reading job postings to infer pain points, then writing a personalized email from scratch.

**SalesAgent compresses this to 45 seconds** — not a CRM with AI bolted on, but an AI agent that *is* the workflow.

---

## What It Does

Paste a LinkedIn URL. The LangGraph agent autonomously runs a 5-step pipeline:

| Step | What happens |
|------|-------------|
| 🔍 **Research** | Calls tools to search company news, analyze job postings for pain points, find tech stack |
| 📊 **Score** | Random Forest ML model scores the lead 0–100 based on profile & company signals |
| ✍️ **Draft** | Writes a hyper-personalized cold email referencing real company events & hiring signals |
| 💾 **Save** | Adds enriched lead + deal to CRM pipeline with auto-scheduled follow-up |
| 🧠 **Remember** | Stores full interaction history for future agent recall |

```
LinkedIn URL → [Research] → [Score] → [Draft Email] → [Pipeline]
                   ↑                                        |
                   └──────── Long-term memory (SQLite) ─────┘
```

---

## Demo Output

**Input:** `https://www.linkedin.com/in/satya-nadella`

**Agent trace (live, ~45 seconds):**
```
🔍 Researching lead from LinkedIn...           ✅ DONE
📊 Scoring lead with ML model...               ✅ DONE  →  90/100
✍️ Drafting personalized cold email...         ✅ DONE
💾 Saving to CRM pipeline...                   ✅ DONE  →  Follow-up: 2026-06-03
```

**Generated email (real output):**
```
Subject: Microsoft Build 2026 — Congrats on the Launch

Satya,

Congrats on the Build 2026 keynote on June 2 — the native Windows AI agent
rollout and the expanded Copilot runtime were a strong signal of where
Microsoft is taking the platform. I noticed your team is actively hiring for
several agent-infrastructure roles this quarter, which tells me you're
scaling this fast...
```

The agent found **real, live company data** — the Microsoft Build 2026 keynote, product launch details, hiring signals — and synthesized it into a fact-first, targeted email. No templates. No placeholders.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | LangGraph (StateGraph + tool-calling loop) |
| LLM | Groq API (`llama-3.1-8b-instant`) |
| Web intelligence | Tavily Search API |
| LinkedIn enrichment | Proxycurl API (optional — fallback works without it) |
| ML lead scoring | scikit-learn (Random Forest) |
| Backend | FastAPI + SQLite |
| Frontend | React + Tailwind |
| Backend deploy | Render |
| Frontend deploy | Streamlit Community Cloud |

---

## What Makes This Agentic

**Real tool-calling** — The LLM receives 4 tool schemas and decides per-step whether and how to call each one. Not a hardcoded pipeline. See `agent/llm.py::run_with_tools`.

**Multi-signal reasoning** — The agent synthesizes company news + job postings + tech stack before writing a single word. Each source informs the output differently.

**Persistent deal memory** — Every interaction is stored in SQLite. Revisit a lead weeks later and the agent has full context: tone used, last touchpoint, company changes.

**Live SSE trace** — Every node streams a Server-Sent Event to the UI in real time, showing exactly what the agent is doing step by step.

---

## Project Structure

```
salesagent/
├── backend/
│   ├── main.py              # FastAPI app — REST + SSE streaming
│   ├── agent/
│   │   ├── state.py         # AgentState TypedDict schema
│   │   ├── graph.py         # LangGraph StateGraph (5 nodes)
│   │   ├── llm.py           # LLM wrapper + agentic tool-calling loop
│   │   └── tools.py         # 4 research tools + JSON schemas
│   ├── memory/
│   │   └── store.py         # SQLite (leads, deals, interactions)
│   ├── ml/
│   │   └── scorer.py        # Random Forest lead scorer
│   ├── tests/
│   │   └── test_smoke.py    # Import/build/output-range smoke tests (CI)
│   └── api/
│       ├── leads.py         # CRUD endpoints
│       ├── deals.py         # Pipeline stage management
│       └── emails.py        # Email regeneration
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── AgentPage.js     # Live agent UI + SSE trace
│       │   ├── PipelinePage.js  # Kanban deal board
│       │   └── LeadsPage.js     # Lead table + detail view
│       └── components/
│           └── Sidebar.js
├── docs/
│   ├── demo-screenshot.png  # Polished before → after product shot
│   └── demo.mp4             # Screen-recorded walkthrough (optional)
├── .github/
│   └── workflows/
│       └── ci.yml           # Runs smoke tests on every push/PR
├── LICENSE
├── render.yaml
└── README.md
```

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/ayush-s-tomar/salesagent.git
cd salesagent

# 2. Backend
cd backend
py -3.11 -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# 3. API keys
cp .env.example .env
# Add GROQ_API_KEY and TAVILY_API_KEY to .env

# 4. Start backend
uvicorn main:app --reload
# → http://localhost:8000/docs

# 5. Frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env          # REACT_APP_API_URL=http://localhost:8000
npm start
# → http://localhost:3000
```

**Free API keys (no credit card required):**
- Groq → https://console.groq.com/keys
- Tavily → https://app.tavily.com
- Proxycurl → https://nubela.co/proxycurl *(optional, $0.01/profile — fallback works without it)*

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent/run` | Run agent on LinkedIn URL (SSE stream) |
| `GET` | `/api/leads/` | List all leads |
| `GET` | `/api/leads/{id}` | Lead detail + interaction history |
| `GET` | `/api/deals/` | All deals with pipeline stages |
| `PATCH` | `/api/deals/{id}/stage` | Move deal to new stage |
| `POST` | `/api/emails/regenerate` | Regenerate email with different tone |

```bash
# Quick test
curl -X POST https://salesagent-ufu7.onrender.com/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/satya-nadella"}'
```

---

## What I'd Add Next

- **Vector memory** (ChromaDB) for semantic lead recall instead of keyword search
- **Gmail integration** to send emails directly from the CRM
- **Multi-agent mode** — separate Research, Scoring, and Writing agents collaborating
- **Fine-tuned email model** trained on high-reply-rate cold email datasets
- **Eval harness** with LLM-as-judge to auto-score email quality

---

## Known Limitations

- **LinkedIn profile scraping is best-effort.** Without a paid Proxycurl key, the agent falls back to inferring names/companies from the URL slug, which can occasionally mismatch (e.g. redirects or vanity URLs that don't match the expected profile). The agent detects and discards mismatched extractions rather than silently using wrong data — see `agent/graph.py::_parse_name_from_url`.
- **Location extraction can produce redundant country tags** (e.g. "India, IN") on certain search result formats — deduped as a post-processing step, but the underlying search API's inconsistency remains.
- **Free-tier LLM rate limits** (Groq) mean heavy concurrent usage may briefly slow or queue email generation.
- **SQLite for persistence** — fine for a portfolio/demo scale, but a production version would move to Postgres for concurrent writes and durability.
- **No authentication layer** — this is a single-user demo; a real CRM deployment would need proper multi-tenant auth before handling real prospect data.

---

*Part of my AI developer portfolio — agents that do real, autonomous work, not chatbots with a prompt. See also: [AgentLoop](https://github.com/ayush-s-tomar/agentloop), a multi-step research agent with tool-use and long-term memory.*
