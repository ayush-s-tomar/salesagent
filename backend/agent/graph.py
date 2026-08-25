import os
import json
import re
import asyncio
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

    profile = state.get("profile", {})
    features = {
        "has_company": 1 if profile.get("company") else 0,
        "has_title": 1 if profile.get("title") else 0,
        "skills_count": len(profile.get("skills", [])),
        "has_summary": 1 if profile.get("summary") else 0,
        "has_news": 1 if state.get("company_news") else 0,
        "has_jobs": 1 if state.get("job_postings") else 0,
    }

    # score_lead now returns {"score": float, "reasons": [str, ...]} instead
    # of a bare float, so the UI can show *why* the lead scored this way
    # (e.g. "High: active news + currently hiring") rather than a naked
    # number with no visible reasoning.
    result = score_lead(features)
    ml_score = result["score"]
    reasons = result["reasons"]

    state["lead_score"] = ml_score
    state["score_reasons"] = reasons

    reason_str = f" ({', '.join(reasons)})" if reasons else ""
    trace.append({"step": "score", "status": "done", "msg": f"Lead score: {ml_score:.0f}/100{reason_str}"})
    state["trace"] = trace
    return state


FORBIDDEN_PLACEHOLDERS = ["[Your Name]", "[Company]", "[Name]", "[Your Company]", "[Position]"]
# FIX: "i noticed you're" only caught one exact phrasing. The model kept
# finding near-miss ways to say the same generic-observation thing —
# "I note Microsoft is hiring across multiple domains" slipped through
# untouched because neither "i noticed" nor "i note" was in the list yet.
# Broadened to catch the family of these openers (any tense/person of
# "notice", plus "I note") rather than one fixed string.
FORBIDDEN_PHRASES = [
    "exciting to see", "impressive", "passion for innovation", "align with your vision",
    "i noticed", "i note", "i've noticed", "i saw", "i came across", "i'm sure you're looking",
    "let's discuss how we can support", "your vision for", "team's focus on",
    "i'd love to", "reach out", "circle back", "touch base",
]
MAX_EMAIL_WORDS = 150

# FIX: matches "Month DD" / "Month DD, YYYY" style dates anywhere in the
# email body, so a generated draft can be checked for whether it invented
# a specific dated event that doesn't actually appear anywhere in the
# real research text passed to the model. This was the concrete failure
# observed in production: a generated email cited a "Jan 26 2026 policy
# extending MAI employee office-commute eligibility" that had no basis in
# the actual company-news/job-postings/tech-stack signals fetched for that
# lead — a fabricated specific dressed up to look like a researched fact.
_MONTH_DATE_PATTERN = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?"
    r"|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+"
    r"\d{1,2}(?:,?\s+\d{4})?\b"
)


def _validate_email(email: str, primary_content: str = "") -> list:
    """Return a list of violation strings, empty if the email is clean."""
    violations = []
    word_count = len(email.split())
    if word_count > MAX_EMAIL_WORDS:
        violations.append(f"Email is {word_count} words, must be under {MAX_EMAIL_WORDS}.")
    for ph in FORBIDDEN_PLACEHOLDERS:
        if ph.lower() in email.lower():
            violations.append(f"Contains forbidden placeholder: {ph}")
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in email.lower():
            violations.append(f"Contains generic filler phrase: '{phrase}'")

    # FIX: fabrication tripwire. Any "Month DD[, YYYY]"-shaped date found in
    # the generated email must also appear verbatim in the source research
    # text (primary_content) — otherwise the model most likely invented it.
    # This is a cheap heuristic, not a full fact-checker: it only catches
    # fabricated *dates*, since that was the observed failure mode, and it
    # can't tell a paraphrased-but-true date from a truly novel one. It's a
    # tripwire to trigger the self-correction retry pass, not a guarantee
    # of full factual accuracy.
    if primary_content:
        for date_match in _MONTH_DATE_PATTERN.finditer(email):
            date_str = date_match.group(0)
            if date_str not in primary_content:
                violations.append(
                    f"References a date not found in the source research: '{date_str}' "
                    "— likely fabricated, not grounded in the primary signal."
                )

    return violations


def _pick_primary_signal(news: str, jobs: str, tech: str) -> tuple:
    """
    Pick ONE dominant intelligence signal to anchor the email around, instead
    of handing the LLM all three and letting it stitch together unrelated
    facts (e.g. a funding number + an internship posting + a product name in
    the same three sentences, which reads as disjointed rather than
    fact-first).

    Priority: news > jobs > tech — a recent news event is the most concrete,
    dated hook; hiring signals are the next-best "why now"; tech stack is the
    weakest/least dated signal so it's used only as a last resort.

    Returns (primary_label, primary_content, supporting_note) — the LLM is
    told to build the ENTIRE email around primary_content, and may only use
    the supporting_note as one secondary detail near the CTA, not as a
    second competing hook.
    """
    if news and news.strip():
        supporting = f"Hiring signal (secondary, one mention max): {jobs[:200]}" if jobs else ""
        return "company news", news, supporting
    if jobs and jobs.strip():
        supporting = f"Tech stack (secondary, one mention max): {tech[:150]}" if tech else ""
        return "hiring signal", jobs, supporting
    if tech and tech.strip():
        return "tech stack", tech, ""
    return "", "", ""


def node_email(state: AgentState) -> AgentState:
    """Generate hyper-personalized cold email, with a self-correction pass
    if the first draft breaks length, placeholder, generic-filler, or
    fabricated-fact rules."""
    trace = state.get("trace", [])
    trace.append({"step": "email", "status": "running", "msg": "Drafting personalized cold email..."})

    profile = state.get("profile", {})
    name = profile.get("name", "there")
    first_name = name.split()[0] if name else "there"
    company = profile.get("company", "") or ""
    title = profile.get("title", "")
    news = state.get("company_news", "")[:500]
    jobs = state.get("job_postings", "")[:400]
    tech = state.get("tech_stack", "")[:300]
    sender_name = os.getenv("SENDER_NAME", "the sender")

    if company:
        company_line = f"at {company}"
    else:
        company_line = "(no company on file - do not invent one, focus on their role/industry instead)"

    primary_label, primary_content, supporting_note = _pick_primary_signal(news, jobs, tech)

    base_prompt = f"""Write a hyper-personalized B2B cold email to {name}, {title} {company_line}.

PRIMARY signal to build the ENTIRE email around ({primary_label}):
{primary_content}

{supporting_note if supporting_note else "(no secondary signal available — use only the primary signal above)"}

HARD RULES:
- The whole email must read as ONE coherent story anchored on the PRIMARY signal above.
  Do NOT give equal weight to multiple unrelated facts — pick the single strongest, most
  specific detail from the primary signal and build the opening, subject line, and body
  around that one thread. The secondary signal (if given) may appear ONCE, briefly, near
  the CTA — never as a second competing hook in the opening or subject line.
- NEVER invent a fact, date, policy, event, product name, or number that is not explicitly
  present in the PRIMARY signal text above. If the primary signal doesn't contain a specific
  enough detail to open with, use the most specific detail it DOES actually contain — do not
  supplement it with a plausible-sounding invented detail. A slightly less punchy TRUE detail
  is always better than a fabricated one, because a fabricated detail can be factually wrong
  and damage credibility with the recipient.
- Open the FIRST sentence with one concrete fact pulled DIRECTLY from the PRIMARY signal text
  above — quote or closely paraphrase something that is actually present in that text, not
  something you infer, extrapolate, or imagine could plausibly be true. Do NOT open with a
  compliment or an observation about "focus" or "vision."
- NEVER use these words/phrases anywhere in the email, even reworded: exciting, impressive, passion,
  align with your vision, I noticed, I note, I saw, I came across, I'm sure you're, let's discuss how
  we can support, reach out, touch base, circle back. These are generic filler — if you catch yourself
  about to write one, replace it with a specific fact instead.
- Every sentence must contain either a specific fact drawn from the intelligence above, or a
  concrete next step. No sentence should be pure sentiment/praise with zero information content,
  and no sentence should introduce a "fact" that isn't traceable back to the intelligence given.
- Subject line: reference the SAME specific fact used in the opening line, not a generic theme,
  and not an invented one.
- Body: connect the primary signal to what the sender's product does, in one sentence — not a
  vague "simplify your operations" claim.
- CTA: one specific, low-friction ask (e.g. a 15-min call Tuesday), not "let's discuss" or "let's chat."
- Length: STRICTLY under {MAX_EMAIL_WORDS} words.
- Sign off with exactly this name: {sender_name} - never use a bracketed placeholder.

Example of the STRUCTURE to hit (this is a template for FORM only — do not reuse or adapt any
of its content; your opening fact must come only from the PRIMARY signal given to you above):
"Subject: [the single specific fact from the PRIMARY signal, stated plainly]
[Name], [that same fact expanded into one sentence, using only wording/details present in the
PRIMARY signal]..."

Return ONLY the email with Subject: on first line."""

    email = chat(
        messages=[{"role": "user", "content": base_prompt}],
        system=(
            "You are an expert B2B sales copywriter known for cutting every generic sentence "
            "and for never mixing more than one intelligence signal into a single email. "
            "You write only what a specific fact justifies — if there's no fact to support a "
            "sentence, you cut the sentence rather than pad it with sentiment. You never "
            "invent a fact, date, or event that was not given to you in the source material, "
            "even if a fabricated one would sound more impressive."
        ),
    )

    violations = _validate_email(email, primary_content)

    if violations:
        trace.append({"step": "email", "status": "running", "msg": f"Draft violated rules, retrying: {violations}"})
        violation_lines = chr(10).join("- " + v for v in violations)
        retry_prompt = f"""Your previous draft violated these rules:
{violation_lines}

Original source intelligence (the ONLY facts you may reference):
---
{primary_content}
---

Previous draft:
---
{email}
---

Rewrite it to fix every violation above. Replace any generic phrase, or any fact/date/event not
present in the original source intelligence above, with a specific detail that IS actually present
in that source text — or cut the sentence entirely if no true detail supports it. Keep the email
anchored on ONE primary signal only. Keep the same length constraint and personalization.
Return ONLY the corrected email with Subject: on first line."""

        email = chat(
            messages=[{"role": "user", "content": retry_prompt}],
            system=(
                "You are an expert B2B sales copywriter known for cutting every generic sentence. "
                "You write only what a specific fact justifies, and you never invent a fact, date, "
                "or event that isn't present in the source material given to you."
            ),
        )

    state["email_draft"] = email
    trace.append({"step": "email", "status": "done", "msg": "Personalized email drafted"})
    state["trace"] = trace
    return state


def node_save(state: AgentState) -> AgentState:
    """Save lead and deal to database."""
    trace = state.get("trace", [])
    trace.append({"step": "save", "status": "running", "msg": "Saving to CRM pipeline..."})

    profile = state.get("profile", {})

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


async def run_agent(
    linkedin_url: str = None,
    message: str = None,
    lead_id: int = None,
) -> AsyncGenerator[dict, None]:
    """Run agent and stream trace events."""
    initial_state: AgentState = {
        "linkedin_url": linkedin_url,
        "message": message,
        "lead_id": lead_id,
        "profile": None,
        "company_news": None,
        "job_postings": None,
        "tech_stack": None,
        "lead_score": None,
        "score_reasons": None,
        "sentiment": None,
        "email_draft": None,
        "deal_id": None,
        "followup_date": None,
        "trace": [],
        "errors": [],
    }

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, graph.invoke, initial_state)

    for event in result.get("trace", []):
        yield event
        await asyncio.sleep(0.1)

    yield {
        "step": "complete",
        "status": "done",
        "msg": "Lead processed successfully",
        "data": {
            "profile": result.get("profile"),
            "score": result.get("lead_score"),
            "score_reasons": result.get("score_reasons"),
            "email": result.get("email_draft"),
            "deal_id": result.get("deal_id"),
            "followup": result.get("followup_date"),
        },
    }


def fresh_state(linkedin_url: str = None, message: str = None, lead_id: int = None) -> AgentState:
    """Build a blank initial state for a new agent run."""
    return {
        "linkedin_url": linkedin_url,
        "message": message,
        "lead_id": lead_id,
        "profile": None,
        "company_news": None,
        "job_postings": None,
        "tech_stack": None,
        "lead_score": None,
        "score_reasons": None,
        "sentiment": None,
        "email_draft": None,
        "deal_id": None,
        "followup_date": None,
        "trace": [],
        "errors": [],
    }