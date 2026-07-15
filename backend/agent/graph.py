import os
import json
import queue
import asyncio
import threading
from typing import AsyncGenerator
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.llm import chat, run_with_tools
from agent.tools import scrape_linkedin_profile, execute_tool
from memory.store import save_lead, get_lead, save_deal, log_interaction
from ml.scorer import score_lead


def _parse_name_from_url(url: str) -> str:
    """Convert LinkedIn URL slug to a readable name."""
    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


def node_research(state: AgentState) -> AgentState:
    """Scrape LinkedIn + gather company intelligence using tool-calling."""
    trace = state.get("trace", [])
    trace.append({"step": "research", "status": "running", "msg": "Researching lead from LinkedIn..."})

    url = state.get("linkedin_url", "")

    system = """You are a B2B sales intelligence agent.
Given a LinkedIn URL, call the available tools to:
1. Call scrape_linkedin_profile with the URL
2. Call search_company_news with the company name you find
3. Call analyze_job_postings with the company name
4. Call find_tech_stack with the company name
Gather as much relevant sales intelligence as possible."""

    text, tool_log = run_with_tools(
        prompt=f"Research this LinkedIn profile and the person's company: {url}",
        system=system,
    )

    profile = {}
    for entry in tool_log:
        if entry["tool"] == "scrape_linkedin_profile":
            try:
                profile = json.loads(entry["result"])
            except Exception:
                profile = {}
        elif entry["tool"] == "search_company_news":
            state["company_news"] = entry["result"]
        elif entry["tool"] == "analyze_job_postings":
            state["job_postings"] = entry["result"]
        elif entry["tool"] == "find_tech_stack":
            state["tech_stack"] = entry["result"]

    if not profile:
        profile = scrape_linkedin_profile(url)

    name = profile.get("name", "")
    if not name or " " not in name:
        profile["name"] = _parse_name_from_url(url)

    if not profile.get("company") or profile.get("company") == "Unknown Company":
        profile["company"] = ""

    state["profile"] = profile
    display_name = profile.get("name", "Lead")
    display_company = profile.get("company") or "their company"
    trace.append({
        "step": "research",
        "status": "done",
        "msg": f"Found: {display_name} at {display_company}"
    })
    state["trace"] = trace
    return state


def node_score(state: AgentState) -> AgentState:
    """Score the lead using ML model."""
    trace = state.get("trace", [])
    trace.append({"step": "score", "status": "running", "msg": "Scoring lead with ML model..."})

    profile = state.get("profile", {}) or {}
    features = {
        "has_company": 1 if profile.get("company") else 0,
        "has_title": 1 if profile.get("title") else 0,
        "skills_count": len(profile.get("skills") or []),
        "has_summary": 1 if profile.get("summary") else 0,
        "has_news": 1 if state.get("company_news") else 0,
        "has_jobs": 1 if state.get("job_postings") else 0,
    }

    ml_score = score_lead(features)
    state["lead_score"] = ml_score

    trace.append({"step": "score", "status": "done", "msg": f"Lead score: {ml_score:.0f}/100"})
    state["trace"] = trace
    return state


FORBIDDEN_PLACEHOLDERS = ["[Your Name]", "[Company]", "[Name]", "[Your Company]", "[Position]"]
MAX_EMAIL_WORDS = 150


def _validate_email(email: str) -> list:
    """Return a list of violation strings, empty if the email is clean."""
    violations = []
    word_count = len(email.split())
    if word_count > MAX_EMAIL_WORDS:
        violations.append(f"Email is {word_count} words, must be under {MAX_EMAIL_WORDS}.")
    for ph in FORBIDDEN_PLACEHOLDERS:
        if ph.lower() in email.lower():
            violations.append(f"Contains forbidden placeholder: {ph}")
    return violations


def node_email(state: AgentState) -> AgentState:
    """Generate hyper-personalized cold email, with a self-correction pass
    if the first draft breaks length or placeholder rules."""
    trace = state.get("trace", [])
    trace.append({"step": "email", "status": "running", "msg": "Drafting personalized cold email..."})

    profile = state.get("profile", {}) or {}
    name = profile.get("name", "there")
    first_name = name.split()[0] if name else "there"
    company = profile.get("company", "") or ""
    title = profile.get("title", "")

    # FIX: state values can be None (key present, tool never called) rather than
    # absent, so `.get(key, "")` does NOT protect against None here — slicing
    # None crashes the whole node. Coerce to "" explicitly before slicing.
    news = (state.get("company_news") or "")[:500]
    jobs = (state.get("job_postings") or "")[:400]
    tech = (state.get("tech_stack") or "")[:300]
    sender_name = os.getenv("SENDER_NAME", "the sender")

    if company:
        company_line = f"at {company}"
    else:
        company_line = "(no company on file - do not invent one, focus on their role/industry instead)"

    base_prompt = f"""Write a hyper-personalized B2B cold email to {name}, {title} {company_line}.

Use this intelligence:
- Company news: {news}
- Hiring signals / pain points: {jobs}
- Tech stack: {tech}

Rules:
- Subject line: reference something specific about them
- Opening: address them as {first_name} (first name only)
- Mention a specific recent company event or initiative, only if real data was provided above
- Body: connect their pain point (from job postings) to a solution
- CTA: simple, one ask, not pushy
- Length: STRICTLY under {MAX_EMAIL_WORDS} words, this is a hard limit
- Tone: professional but human, not salesy
- Sign off with exactly this name: {sender_name} - never use a bracketed placeholder for the sender name, company, or anything else

Return ONLY the email with Subject: on first line."""

    email = chat(
        messages=[{"role": "user", "content": base_prompt}],
        system="You are an expert B2B sales copywriter. Write emails that get replies.",
    )

    violations = _validate_email(email)

    if violations:
        trace.append({"step": "email", "status": "running", "msg": f"Draft violated rules, retrying: {violations}"})
        violation_lines = chr(10).join("- " + v for v in violations)
        retry_prompt = f"""Your previous draft violated these rules:
{violation_lines}

Previous draft:
---
{email}
---

Rewrite it to fix every violation above. Keep the same personalization and quality,
just fix the specific issues listed. Return ONLY the corrected email with Subject: on first line."""

        email = chat(
            messages=[{"role": "user", "content": retry_prompt}],
            system="You are an expert B2B sales copywriter. Write emails that get replies.",
        )

    state["email_draft"] = email
    trace.append({"step": "email", "status": "done", "msg": "Personalized email drafted"})
    state["trace"] = trace
    return state


def node_save(state: AgentState) -> AgentState:
    """Save lead and deal to database."""
    trace = state.get("trace", [])
    trace.append({"step": "save", "status": "running", "msg": "Saving to CRM pipeline..."})

    profile = state.get("profile", {}) or {}

    lead_id = save_lead({
        "name": profile.get("name", "Unknown"),
        "title": profile.get("title", ""),
        "company": profile.get("company", ""),
        "location": profile.get("location", ""),
        "linkedin_url": profile.get("linkedin_url", ""),
        "score": state.get("lead_score", 0),
        "email_draft": state.get("email_draft", ""),
        "stage": "Lead",
    })

    deal_id = save_deal({
        "lead_id": lead_id,
        "title": f"{profile.get('name', 'Lead')} - {profile.get('company', '')}",
        "stage": "Lead",
        "score": state.get("lead_score", 0),
    })

    followup = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    state["deal_id"] = deal_id
    state["followup_date"] = followup

    log_interaction(lead_id, "agent_research", state.get("email_draft", ""))

    trace.append({"step": "save", "status": "done", "msg": f"Added to pipeline. Follow-up: {followup}"})
    state["trace"] = trace
    return state


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("research", node_research)
    g.add_node("score", node_score)
    g.add_node("email", node_email)
    g.add_node("save", node_save)

    g.set_entry_point("research")
    g.add_edge("research", "score")
    g.add_edge("score", "email")
    g.add_edge("email", "save")
    g.add_edge("save", END)
    return g.compile()


graph = build_graph()


def fresh_state(linkedin_url: str = None, message: str = None, lead_id: int = None) -> AgentState:
    """Build a clean initial state dict for a new agent run."""
    return {
        "linkedin_url": linkedin_url,
        "message": message,
        "lead_id": lead_id,
        "profile": None,
        "company_news": None,
        "job_postings": None,
        "tech_stack": None,
        "lead_score": None,
        "sentiment": None,
        "email_draft": None,
        "deal_id": None,
        "followup_date": None,
        "trace": [],
        "errors": [],
    }


_SENTINEL = object()


async def run_agent(
    linkedin_url: str = None,
    message: str = None,
    lead_id: int = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the agent and stream trace events AS THEY HAPPEN.

    FIX: the previous version called graph.invoke() (blocking until the whole
    pipeline finished, ~30-45s) and only then replayed the stored trace with
    artificial sleeps — so the SSE stream looked instant-then-silent instead
    of live. This version runs graph.stream() in a background thread and
    forwards each new trace entry to the async generator the moment it's
    produced, via a thread-safe queue, so the frontend gets genuinely
    incremental progress.
    """
    initial_state = fresh_state(linkedin_url=linkedin_url, message=message, lead_id=lead_id)

    q: "queue.Queue" = queue.Queue()

    def _worker():
        try:
            emitted = 0
            final_state = initial_state
            for chunk in graph.stream(initial_state, stream_mode="updates"):
                node_name, node_state = next(iter(chunk.items()))
                final_state = node_state
                trace = node_state.get("trace", [])
                # Only forward entries we haven't emitted yet (a node may log
                # more than one trace line, e.g. "running" then "done", or an
                # extra "retrying" line in node_email).
                for entry in trace[emitted:]:
                    q.put(entry)
                emitted = len(trace)
            q.put({
                "step": "complete",
                "status": "done",
                "msg": "Lead processed successfully",
                "data": {
                    "profile": final_state.get("profile"),
                    "score": final_state.get("lead_score"),
                    "email": final_state.get("email_draft"),
                    "deal_id": final_state.get("deal_id"),
                    "followup": final_state.get("followup_date"),
                },
            })
        except Exception as e:
            q.put({"step": "error", "status": "error", "msg": str(e)})
        finally:
            q.put(_SENTINEL)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    while True:
        item = await loop.run_in_executor(None, q.get)
        if item is _SENTINEL:
            break
        yield item