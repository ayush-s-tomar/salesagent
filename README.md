# SalesAgent — Autonomous B2B Sales AI

> Paste a LinkedIn URL. Get a researched lead, ML score, and personalized cold email in 45 seconds.

**🔗 Live Demo** · [salesagent.onrender.com](https://salesagent.onrender.com)

---

## What It Does

Most CRMs bolt AI onto existing workflows. SalesAgent is different — the AI agent **is** the workflow.

Give it a LinkedIn URL. The agent runs a 5-step pipeline autonomously:

| Step | What happens |
|------|-------------|
| **Research** | Scrapes LinkedIn profile, searches company news, analyzes job postings for pain points, finds tech stack |
| **Score** | ML model (Random Forest) scores the lead 0–100 based on profile completeness & company signals |
| **Draft** | Writes a hyper-personalized cold email referencing specific company events, hiring signals & tech stack |
| **Save** | Adds enriched lead + deal to CRM pipeline with auto-scheduled follow-up |
| **Persist** | Stores interaction history for future agent recall |

```
LinkedIn URL → Research → Score → Draft Email → Pipeline
                ↑                                    |
                └──── Long-term memory (SQLite) ─────┘
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | LangGraph (StateGraph + conditional edges) |
| LLM + tool-calling | Groq (llama-3.3-70b-versatile) |
| Web intelligence | Tavily API |
| LinkedIn data | Proxycurl API (optional) |
| ML lead scoring | scikit-learn (Random Forest) |
| Backend | FastAPI + SQLite |
| Frontend | React |
| Deploy | Render |

---

## What Makes This Agentic

**Real tool-calling** — The LLM is given 4 tool schemas and decides per-step whether and how to call each one. Not a hardcoded pipeline. See `agent/llm.py::run_with_tools`.

**Multi-signal reasoning** — The agent synthesizes LinkedIn data + company news + job postings + tech stack before writing a single word of the email. Each source informs the output differently.

**Persistent deal memory** — Every lead interaction is stored in SQLite. Revisit a lead weeks later and the agent has full context: tone used, last touchpoint, company changes.

**Live trace** — Every node emits a Server-Sent Event that streams to the UI in real time, showing exactly what the agent is doing.

---

## Project Structure

```
salesagent/
├── backend/
│   ├── main.py              FastAPI app — REST + SSE streaming
│   ├── agent/
│   │   ├── state.py         AgentState schema
│   │   ├── graph.py         LangGraph StateGraph (5 nodes)
│   │   ├── llm.py           LLM wrapper + tool-calling loop
│   │   └── tools.py         4 research tools + schemas
│   ├── memory/
│   │   └── store.py         SQLite (leads, deals, interactions)
│   ├── ml/
│   │   └── scorer.py        Random Forest lead scorer
│   └── api/
│       ├── leads.py         CRUD endpoints
│       ├── deals.py         Pipeline stage management
│       └── emails.py        Email regeneration
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── AgentPage.js     Live agent UI + SSE trace
│       │   ├── PipelinePage.js  Kanban deal board
│       │   └── LeadsPage.js     Lead table + detail view
│       └── components/
│           └── Sidebar.js
├── render.yaml
└── README.md
```

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/salesagent.git
cd salesagent

# 2. Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. API keys
cp .env.example .env
# Edit .env — add GROQ_API_KEY and TAVILY_API_KEY

# 4. Start backend
uvicorn main:app --reload
# → http://localhost:8000

# 5. Frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env              # REACT_APP_API_URL=http://localhost:8000
npm start
# → http://localhost:3000
```

**Free API keys (no credit card):**
- Groq → https://console.groq.com/keys
- Tavily → https://app.tavily.com
- Proxycurl → https://nubela.co/proxycurl (optional, paid — fallback works without it)

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent/run` | Run agent on LinkedIn URL (SSE stream) |
| `GET` | `/api/leads/` | List all leads |
| `GET` | `/api/leads/{id}` | Lead detail + interaction history |
| `GET` | `/api/deals/` | All deals with stages |
| `PATCH` | `/api/deals/{id}/stage` | Move deal to new stage |
| `POST` | `/api/emails/regenerate` | Regenerate email with different tone |

```bash
# Example
curl -X POST https://your-app.onrender.com/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/satya-nadella"}'
```

---

## What I'd Add Next

- **Vector memory** (ChromaDB) instead of SQLite keyword recall
- **Gmail integration** to send emails directly from the CRM
- **Multi-agent mode** — separate Research, Scoring, and Writing agents collaborating
- **Fine-tuned email model** trained on high-reply-rate cold emails
- **Eval harness** with LLM-as-judge to score email quality automatically

---

## Why I Built This

Manual B2B lead research takes 1–2 hours per lead: checking LinkedIn, Googling company news, reading job postings to infer pain points, then writing a personalized email. SalesAgent compresses this to 45 seconds using a real agentic AI pipeline — not just an LLM wrapper.

Built to demonstrate: LangGraph agent architecture, real tool-calling, ML model integration in a production API, and full-stack deployment.

---

*See also: [AgentLoop](https://github.com/ayush-s-tomar/agentloop) — multi-step research agent with memory*
