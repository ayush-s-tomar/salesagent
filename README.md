# SalesAgent — Autonomous B2B Sales AI

![Python](https://img.shields.io/badge/python-3.11-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![FastAPI](https://img.shields.io/badge/FastAPI-backend-teal) ![React](https://img.shields.io/badge/React-frontend-61dafb) ![Status](https://img.shields.io/badge/status-CI%20passing-brightgreen)

An AI agent that researches a lead, scores them, and writes a personalized cold email — in 45 seconds, from just a LinkedIn URL.

🔗 [Live Demo (frontend)](https://salesagent-frontend-jwar.onrender.com)  |  📝 Technical Writeup  |  👤 [LinkedIn](https://www.linkedin.com/in/ayushsinghtomar/)  |  💻 [GitHub](https://github.com/ayush-s-tomar/salesagent)

> **Note:** Backend and frontend are both on Render's free tier, so the backend may take 30–60s to wake up on first use. If it's mid cold-start, the demo video below shows the full flow.

**SalesAgent — one URL in, a scored, personalized lead out**

One URL in. A scored, personalized lead out — in ~45 seconds.

**SalesAgent — live agent trace walkthrough**

Live agent trace — research → score → draft → save, end to end.

## 🎥 Demo Video
`SalesAgent.Demo.mp4`

## Why I Built This

I was spending 1–2 hours per lead doing manual research before writing a single cold email — checking LinkedIn, Googling company news, digging through job postings for pain points. It felt like exactly the kind of multi-step, tool-using task an LLM agent should own end-to-end, not just assist with. So I built one that does the whole loop: research → score → draft → save → remember.

## The Problem

Manual B2B lead research takes 1–2 hours per lead: checking LinkedIn, Googling company news, reading job postings to infer pain points, then writing a personalized email from scratch.

SalesAgent compresses this to 45 seconds — not a CRM with AI bolted on, but an AI agent that is the workflow.

## What It Does

Paste a LinkedIn URL. The LangGraph agent autonomously runs a 5-step pipeline:

| Step | What happens |
|---|---|
| 🔍 Research | Calls tools to search company news, analyze job postings for pain points, find tech stack |
| 📊 Score | Random Forest ML model scores the lead 0–100 based on profile & company signals |
| ✍️ Draft | Writes a hyper-personalized cold email referencing real company events & hiring signals |
| 💾 Save | Adds enriched lead + deal to CRM pipeline with auto-scheduled follow-up |
| 🧠 Remember | Stores full interaction history for future agent recall |

```
LinkedIn URL → [Research] → [Score] → [Draft Email] → [Pipeline]
                   ↑                                        |
                   └──────── Long-term memory (SQLite) ─────┘
```

The scorer is a Random Forest trained on 6 features (`has_company`, `has_title`, `skills_count`, `has_summary`, `has_news`, `has_jobs`) — weighted so active news coverage and open job postings count most (30% + 25% combined), since those best signal a company that's actively growing right now. It's trained on synthetic data with hand-set weights rather than real historical deal outcomes — a real production version would retrain this on actual won/lost CRM data. See `ml/scorer.py::train_and_save`.

## Demo Output

**Input:** `https://www.linkedin.com/in/satya-nadella`

**Agent trace (live, ~45 seconds):**

```
🔍 Researching lead from LinkedIn...           ✅ DONE  →  Found: Satya Nadella at Microsoft
📊 Scoring lead with ML model...               ✅ DONE  →  90/100
✍️ Drafting personalized cold email...         ✅ DONE
💾 Saving to CRM pipeline...                   ✅ DONE  →  Follow-up: auto-scheduled
```

**Generated email (real output):**

```
Subject: August 13, 2026 — Senior/Principal Product Systems Engineer posting

Satya, the August 13 2026 posting for a Senior/Principal Product Systems
Engineer in Cambridge cites AI, systems and networking research as core
responsibilities. Our release-planner analytics platform pulls the Microsoft
release planner tool data for Oct 2025–Mar 2026 and auto-generates
engineer-specific feature views, cutting manual build-up time by 40% in
internal tests...
```

The agent found real, live company data — an active engineering job posting, its specific responsibilities and location — and synthesized it into a fact-first, targeted email tied to a concrete hiring signal. No templates. No placeholders.

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph (StateGraph + tool-calling loop) |
| LLM | Groq API (`openai/gpt-oss-120b`) |
| Web intelligence | Tavily Search API |
| LinkedIn enrichment | Proxycurl API (optional — fallback works without it) |
| ML lead scoring | scikit-learn (Random Forest) |
| Backend | FastAPI + SQLite |
| Frontend | React + Tailwind |
| Backend deploy | Render |
| Frontend deploy | Render (Static Site) |

## What Makes This Agentic

**Real tool-calling** — The LLM receives 4 tool schemas and decides per-step whether and how to call each one. Not a hardcoded pipeline. See `agent/llm.py::run_with_tools`.

**Multi-signal reasoning** — The agent synthesizes company news + job postings + tech stack before writing a single word. Each source informs the output differently.

**Persistent deal memory** — Every interaction is stored in SQLite. Revisit a lead weeks later and the agent has full context: tone used, last touchpoint, company changes.

**Live SSE trace** — Every node streams a Server-Sent Event to the UI in real time, showing exactly what the agent is doing step by step.

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
│   ├── demo.gif             # Live agent trace walkthrough (GIF preview)
│   └── demo.mp4             # Screen-recorded walkthrough
├── .github/
│   └── workflows/
│       └── ci.yml           # Runs smoke tests on every push/PR
├── LICENSE
├── render.yaml
└── README.md
```

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
- Proxycurl → https://nubela.co/proxycurl (optional, $0.01/profile — fallback works without it)

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/agent/run` | Run agent on LinkedIn URL (SSE stream) |
| GET | `/api/leads/` | List all leads |
| GET | `/api/leads/{id}` | Lead detail + interaction history |
| GET | `/api/deals/` | All deals with pipeline stages |
| PATCH | `/api/deals/{id}/stage` | Move deal to new stage |
| POST | `/api/emails/regenerate` | Regenerate email with different tone |

```bash
# Quick test (after running the backend locally — see "Run Locally" above)
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/satya-nadella"}'
```

## What I'd Add Next

- **Retrain the scorer on real outcomes** — swap the synthetic hand-weighted training data for actual won/lost deal history once there's enough volume, so the model learns real signal instead of my guessed weights
- **Tighten LinkedIn extraction** — replace the URL-slug fallback with a more reliable enrichment path so `_parse_name_from_url` mismatches (see Known Limitations) become rarer
- **Wire up `evals/judge.py` in CI** — the LLM-as-judge scorer already exists locally; next step is running it automatically on every PR so email-quality regressions get caught before merge, not after
- **Postgres migration** — move off SQLite once this needs concurrent writes from more than one user
- **Gmail integration** — send drafted emails directly from the CRM instead of copy-paste

## Known Limitations

- LinkedIn profile scraping is best-effort. Without a paid Proxycurl key, the agent falls back to inferring names/companies from the URL slug, which can occasionally mismatch (e.g. redirects or vanity URLs that don't match the expected profile). The agent detects and discards mismatched extractions rather than silently using wrong data — see `agent/graph.py::_parse_name_from_url`.
- Location extraction can produce redundant country tags (e.g. "India, IN") on certain search result formats — deduped as a post-processing step, but the underlying search API's inconsistency remains.
- Free-tier LLM rate limits (Groq) mean heavy concurrent usage may briefly slow or queue email generation.
- SQLite for persistence — fine for a portfolio/demo scale, but a production version would move to Postgres for concurrent writes and durability.
- No authentication layer — this is a single-user demo; a real CRM deployment would need proper multi-tenant auth before handling real prospect data.
- Free-tier hosting — both backend and frontend run on Render's free tier, so the backend spins down after inactivity. Expect a cold-start delay of 30–60s on first use. Happy to spin up a dedicated live instance on request.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/ayush-s-tomar/salesagent/issues).

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙋 Author

**Ayush Singh Tomar** — [GitHub](https://github.com/ayush-s-tomar)

Part of my AI developer portfolio — agents that do real, autonomous work, not chatbots with a prompt. See also: AgentLoop, a multi-step research agent with tool-use and long-term memory.
