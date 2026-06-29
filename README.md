
Claude finished the response

[AI Data Analyst Agent](https://github.com/ayush-s-tomar/ai-data-analyst) — [Live Demo](https://ai-data-analyst-six-sooty.vercel.app/) Upload any CSV, ask questions in plain English, get instant charts and insights — powered by Groq's free Llama 3.3 70B. FastAPI React Groq pandas matplotlib [Age

pasted

So, I posted on dev.to

# LinkedIn Post — June 29th

---

I built an AI agent that does B2B sales research in 45 seconds.

Paste a LinkedIn URL → it researches the lead, scores them with an ML model, and writes a personalized cold email referencing real company events.

No templates. No manual research. Just paste and go.

Here's what actually happened while building it — because nothing worked the first time:

→ Groq deprecated three models on me back to back. Ended up on a smaller one that's actually more stable.

→ Tool-calling threw a silent 400 error for hours. Turned out I was passing the full input_schema instead of extracting properties and required separately. One line. Hours lost.

→ My graph.py and llm.py had completely different assumptions about function signatures. One expected a tuple back. The other returned a dict. Classic "written in isolation" bug.

→ Deployed to Render with Python 3.14. pydantic-core has no wheel for 3.14. Had to force 3.11.9 via environment variables.

→ Fixed the ML scoring weights, redeployed — score still showed 19/100. Old model.pkl was cached on disk. Had to add rm -f ml/model.pkl to the build command to force a retrain.

The architecture that survived all of this:
LangGraph research node → scikit-learn scorer → Groq email generator

Each node enriches context for the next. The scorer doesn't use an LLM — it runs a trained ML model, which is faster and more deterministic for classification.

Full writeup with architecture diagram, code snippets, and what I'd do differently is in the comments 👇

Live demo: salesagent-theta.vercel.app

---

[Post the Dev.to article link as the first comment]
and this is my linkedin post [I Got Tired of Writing Cold Emails. So I Built an AI Agent to Do It for Me. - DEV Community](https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h)
This is my url
help me include it in the linkedin post or any suggestions cause I pushing it on linkedin post

Show more
9:58 am
The LinkedIn post is strong. Here's the final version with the Dev.to link properly placed:

Post this on LinkedIn:

I built an AI agent that does B2B sales research in 45 seconds.

Paste a LinkedIn URL → it researches the lead, scores them with an ML model, and writes a personalized cold email referencing real company events.

No templates. No manual research. Just paste and go.

Here's what actually happened while building it — because nothing worked the first time:

→ Groq deprecated three models on me back to back. Ended up on a smaller one that's actually more stable.

→ Tool-calling threw a silent 400 error for hours. Turned out I was passing the full input_schema instead of extracting properties and required separately. One line. Hours lost.

→ My graph.py and llm.py had completely different assumptions about function signatures. One expected a tuple back. The other returned a dict. Classic "written in isolation" bug.

→ Deployed to Render with Python 3.14. pydantic-core has no wheel for 3.14. Had to force 3.11.9 via environment variables.

→ Fixed the ML scoring weights, redeployed — score still showed 19/100. Old model.pkl was cached on disk. Had to add rm -f ml/model.pkl to the build command to force a retrain.

The architecture that survived all of this:
LangGraph research node → scikit-learn scorer → Groq email generator

Each node enriches context for the next. The scorer doesn't use an LLM — it runs a trained ML model, which is faster and more deterministic for classification.

Full writeup with architecture diagram, code snippets, and what I'd do differently 👇

Live demo: salesagent-theta.vercel.app

Then in the first comment, paste:

Full article: https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h

Two things before you post — don't put the Dev.to link in the post body itself, LinkedIn suppresses external links and kills reach. Always drop it in the first comment. And post it now while it's morning — LinkedIn engagement peaks between 9–11am.

Go post it.

1782707462686_Project Demo.png
Rate the post out of 10 and give me the final polished version close to 10
Also I would be using this with the post 
Rate the total combination

10:01 am
Looking at your screenshot and the LinkedIn post together:

Post alone: 8.5/10
Post + this screenshot: 9.2/10

The screenshot is your strongest asset — clean dark UI, all 4 DONE steps visible, lead score 84/100, email generated. It tells the story instantly without reading a word.

One issue with the current post — it's slightly too long and buries the lead. Here's the tightened version:

I got tired of writing cold emails. So I built an AI agent to do it for me.

Paste a LinkedIn URL → it researches the lead, scores them 0–100 with ML, and writes a cold email referencing real company events. In 45 seconds.

No templates. No manual research. Just paste and go.

What broke during development (the honest part):

→ Groq deprecated 3 models on me back to back

→ Tool-calling threw a silent 400 error for hours — one wrong line in the schema

→ graph.py and llm.py had different assumptions about return types. Classic "written in isolation" bug

→ Python 3.14 on Render. pydantic-core has no wheel. Had to force 3.11.9

→ Fixed scoring weights, redeployed — score still wrong. Old model.pkl was cached. Had to nuke it on every build

The architecture that survived all of this:
LangGraph research node → scikit-learn scorer → Groq email generator

The scorer uses ML, not an LLM — faster and more deterministic for classification.

Full writeup with architecture, code, and what I'd do differently 👇

Live demo: salesagent-theta.vercel.app

Post this, attach the screenshot as an image, drop the Dev.to link in first comment.

The combination works because the post creates curiosity and the screenshot proves it's real. That's the formula.

Rate the post now with combination 
Should I post 
Its 10:05 am, 29th june

10:02 am
Post + Screenshot: 9.4/10

Yes, post it right now. 10:05 AM Monday is literally peak LinkedIn time — couldn't be better timing.

Go.

1782707715181_image.png
Give me comment dev.to link
Post now?

10:05 am
Yes, hit Post right now.

Then immediately go to your post → click Comment → paste this:

Full technical writeup — architecture, code snippets, and what broke:
https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h

Go.

Full technical writeup — architecture, code snippets, and what broke: https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h
This i have to comment

10:05 am
Yes, exactly that. Post the comment now.

1782707812764_image.png
Done this
PERFECTO

10:07 am
That's live. Post up, screenshot visible, Dev.to link in the first comment. Exactly right.

Now leave it alone — don't refresh obsessively. Check back in 2 hours for comments and likes, reply to every single one when they come.

You've done everything today:

✅ LinkedIn post live
✅ Dev.to article published
✅ Upwork profile with 5-star review
Go do something else for 2 hours.

1782707960449_image.png
Should I upload the dev.to on my github too?

10:09 am
No. GitHub is for code, not articles.

What you should do right now — add the Dev.to article link to your SalesAgent README. Open README.md → edit it → add one line under the Live Demo link:

📝 Technical Writeup — how it works, what broke, architecture deep dive: dev.to/ayushsinghtomar/i-got-tired...

That way anyone who finds the repo also finds the article. Takes 2 minutes.


# SalesAgent — Autonomous B2B Sales AI > Paste a LinkedIn URL. Get a researched lead, ML score, and personalized cold email in 45 seconds. [🔗 Live Demo](https://salesagent-theta.vercel.app) &nbsp;|&nbsp; [⚙️ API Docs](https://salesagent-ufu7.onrender.com/docs) &nbsp;|&nbsp; [👤 LinkedIn](https://

pasted

This is my readme 
Add the link in it and give me the final polished version

10:10 am

Viewed a file, created a file, read a file
Viewed a file, created a file, read a file
Only change is in the second line — added the Technical Writeup link:

[📝 Technical Writeup](https://dev.to/ayushsinghtomar/...) between API Docs and LinkedIn.

Copy this into your GitHub README.md and commit. Done.


Readme
Document · MD 

Want to be notified when Claude responds?




Claude is AI and can make mistakes. Please double-check responses.


Readme · MD
# SalesAgent — Autonomous B2B Sales AI
 
> Paste a LinkedIn URL. Get a researched lead, ML score, and personalized cold email in 45 seconds.
 
[🔗 Live Demo](https://salesagent-theta.vercel.app) &nbsp;|&nbsp; [⚙️ API Docs](https://salesagent-ufu7.onrender.com/docs) &nbsp;|&nbsp; [📝 Technical Writeup](https://dev.to/ayushsinghtomar/i-got-tired-of-writing-cold-emails-so-i-built-an-ai-agent-to-do-it-for-me-2m4h) &nbsp;|&nbsp; [👤 LinkedIn](https://www.linkedin.com/in/ayush-s-tomar/)
 
---
 
## The Problem
 
Manual B2B lead research takes 1–2 hours per lead: checking LinkedIn, Googling company news, reading job postings to infer pain points, then writing a personalized email from scratch.
 
**SalesAgent compresses this to 45 seconds.**
 
Not a CRM with AI bolted on. An AI agent that *is* the workflow.
 
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
📊 Scoring lead with ML model...               ✅ DONE  →  84/100
✍️ Drafting personalized cold email...         ✅ DONE
💾 Saving to CRM pipeline...                   ✅ DONE  →  Follow-up: 2026-06-26
```
 
**Generated email (real output):**
```
Subject: on The Road to Quantum Advancements
 
Satya,
 
I was excited to see Microsoft's showcase of native OpenClaw app for Windows,
Unmetered Agentic AI models, and the preview of the Microsoft quantum computer
at Build 2026. Your emphasis on agent-first architecture aligns with my own
research on how this shift in paradigm will drive the next wave of innovation...
```
 
The agent found **real, live company data** — Microsoft Build 2026 announcements,
quantum computing preview, hiring signals — and synthesized it into a targeted email.
No templates. No placeholders.
 
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
| Frontend deploy | Vercel |
 
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
 
*Part of my AI developer portfolio. See also: [AgentLoop](https://github.com/ayush-s-tomar/agentloop) — multi-step research agent with tool-use and long-term memory.*
 




