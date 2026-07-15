import os
import json
import httpx
from typing import Optional
from tavily import TavilyClient
from groq import Groq

# FIX: both clients used to be constructed at MODULE IMPORT TIME:
#   tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
#   groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
# TavilyClient raises immediately if the key is empty — so simply doing
# `import agent.tools` (e.g. from mcp_server/server.py, which never calls
# load_dotenv() itself) crashed before any function in this file was even
# called, regardless of whether that function needed Tavily at all.
# Lazy singletons defer construction to first real use, after whatever
# entry point (main.py, streamlit_app.py, mcp_server/server.py) has had a
# chance to load environment variables.
_tavily_client: Optional[TavilyClient] = None
_groq_client: Optional[Groq] = None


def _tavily() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
    return _tavily_client


def _groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    return _groq_client


EXTRACT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def scrape_linkedin_profile(linkedin_url: str) -> dict:
    """
    Scrape public LinkedIn profile data.
    Uses Proxycurl API if key is set. Otherwise, falls back to a Tavily
    web search on the profile URL + name, then uses an LLM to extract
    structured fields from the search snippets. This fallback returns
    real, varying data instead of blank fields for every profile.
    """
    api_key = os.getenv("PROXYCURL_API_KEY", "")

    if api_key:
        try:
            resp = httpx.get(
                "https://nubela.co/proxycurl/api/v2/linkedin",
                params={"url": linkedin_url},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                    "title": data.get("occupation", ""),
                    "company": data.get("experiences", [{}])[0].get("company", "") if data.get("experiences") else "",
                    "location": _clean_location(data.get("city", "")),
                    "summary": data.get("summary", ""),
                    "skills": [s.get("name", "") for s in data.get("skills", [])[:10]],
                    "linkedin_url": linkedin_url,
                    "source": "proxycurl",
                }
        except Exception as e:
            print(f"Proxycurl error: {e}")

    # Fallback: derive name from URL slug, then search for real signal
    slug = linkedin_url.rstrip("/").split("/")[-1]
    fallback_name = slug.replace("-", " ").title()

    return _search_based_profile(linkedin_url, fallback_name)


def _clean_location(location: str) -> str:
    """
    Dedupe redundant country mentions in extracted location strings, e.g.
    "Mountain View, California, United States, US" -> "Mountain View,
    California, United States". The LLM extraction sometimes pulls both the
    full country name and its abbreviation from the same source snippet
    (a state's official abbreviation, or a country code tacked onto the end
    by whatever page Tavily indexed) and includes both, which reads as a
    typo-like repeat rather than genuinely new information.
    """
    if not location or not location.strip():
        return location

    COUNTRY_ALIASES = {
        "US": "United States", "USA": "United States", "U.S.": "United States", "U.S.A.": "United States",
        "UK": "United Kingdom", "U.K.": "United Kingdom",
        "UAE": "United Arab Emirates",
    }

    parts = [p.strip() for p in location.split(",") if p.strip()]
    cleaned = []
    seen_normalized = set()
    for part in parts:
        normalized = COUNTRY_ALIASES.get(part.upper().rstrip("."), part).lower()
        if normalized in seen_normalized:
            continue
        seen_normalized.add(normalized)
        cleaned.append(part)

    return ", ".join(cleaned)


def _search_based_profile(linkedin_url: str, fallback_name: str) -> dict:
    """
    No Proxycurl key: use Tavily to search for this specific LinkedIn URL,
    then ask an LLM to extract name/title/company/location from the
    snippets. Falls back to slug-only data if search returns nothing
    useful, but never silently returns identical blank data for every
    profile the way the old fallback did.
    """
    try:
        # FIX: previous query used `"{linkedin_url}" OR "{fallback_name}" linkedin
        # profile title company` — the OR let Tavily match ANY page containing
        # generic words like "linkedin"/"profile"/"company", not necessarily
        # this person. That's how a search for satya-nadella's profile came
        # back with an article about Ryan Roslansky (LinkedIn's own CEO) —
        # it matched on the word "linkedin", not the actual person.
        # Now: both the URL and the name are required (implicit AND), and
        # results are restricted to linkedin.com so unrelated news articles
        # can't be picked up at all.
        #
        # FIX (location): added "location city" to the query terms so Tavily
        # is more likely to surface snippets that actually mention where the
        # person is based (previously the query only asked for title/company,
        # so location almost never showed up in the returned snippets even
        # though the extraction prompt below always asks for it).
        # Also bumped max_results 5 -> 8 and added search_depth="advanced",
        # which pulls fuller page content instead of short snippets — location
        # is often buried below the fold on a LinkedIn snippet, not in the
        # first line Tavily would otherwise return.
        results = _tavily().search(
            query=f'"{linkedin_url}" "{fallback_name}" title company location city current role',
            max_results=8,
            search_depth="advanced",
            include_domains=["linkedin.com"],
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        combined = " ".join(snippets)[:3000]
    except Exception as e:
        combined = ""
        print(f"Tavily profile search error: {e}")

    if not combined.strip():
        return {
            "name": fallback_name,
            "title": "Professional",
            "company": "",
            "location": "",
            "summary": "",
            "skills": [],
            "linkedin_url": linkedin_url,
            "source": "slug_only_no_search_results",
        }

    extraction_prompt = f"""Extract structured profile info from this web search text about
a LinkedIn profile. If a field genuinely cannot be found, use an empty string (not a guess).

SEARCH TEXT:
{combined}

FALLBACK NAME (from URL slug, use only if no better name is found): {fallback_name}

Return ONLY valid JSON, no markdown fences, no preamble, in this exact shape:
{{
  "name": "",
  "title": "",
  "company": "",
  "location": "",
  "summary": "",
  "skills": []
}}"""

    try:
        resp = _groq().chat.completions.create(
            model=EXTRACT_MODEL,
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=500,
            temperature=0,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        extracted = json.loads(raw)

        # FIX: safety net in case the search still drifts off-target despite
        # the tighter query above. If the name the LLM extracted doesn't
        # loosely match the name we expect from the URL slug, discard the
        # extraction entirely rather than silently returning a stranger's
        # profile data under this person's URL.
        #
        # FIX (no-hyphen slugs): URL slugs without hyphens (e.g.
        # "sundarpichai") produce a fallback name with no space
        # ("sundarpichai"), while the LLM correctly extracts "sundar pichai"
        # WITH a space. Neither string is a substring of the other once one
        # has a space and the other doesn't, so the correct extraction was
        # being discarded as a "mismatch". Comparing with spaces stripped
        # from both sides fixes this while still catching genuine mismatches
        # like the Ryan Roslansky case.
        extracted_name = (extracted.get("name") or "").strip().lower()
        fallback_lower = fallback_name.strip().lower()
        extracted_compact = extracted_name.replace(" ", "")
        fallback_compact = fallback_lower.replace(" ", "")
        if extracted_name and not (
            extracted_compact in fallback_compact or fallback_compact in extracted_compact
        ):
            print(
                f"Name mismatch: extracted '{extracted_name}' vs expected "
                f"'{fallback_lower}' for {linkedin_url}, discarding extraction"
            )
            extracted = {}

    except json.JSONDecodeError:
        print(f"Profile extraction: model returned non-JSON for {linkedin_url}, using fallback name only.")
        extracted = {}
    except Exception as e:
        print(f"Profile extraction error for {linkedin_url}: {type(e).__name__}: {e}")
        extracted = {}

    return {
        "name": extracted.get("name") or fallback_name,
        "title": extracted.get("title") or "Professional",
        "company": extracted.get("company") or "",
        "location": _clean_location(extracted.get("location") or ""),
        "summary": extracted.get("summary") or "",
        "skills": extracted.get("skills") or [],
        "linkedin_url": linkedin_url,
        "source": "tavily_search_extraction",
    }


def search_company_news(company_name: str) -> str:
    """Search for latest company news, funding, product launches."""
    if not company_name or not company_name.strip():
        return "No company name available to search news for."
    try:
        results = _tavily().search(
            query=f"{company_name} latest news funding product launch 2025 2026",
            max_results=3,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:1500]
    except Exception as e:
        return f"Could not fetch news: {e}"


def analyze_job_postings(company_name: str) -> str:
    """Find pain points by analyzing what roles the company is hiring for."""
    if not company_name or not company_name.strip():
        return "No company name available to search job postings for."
    try:
        results = _tavily().search(
            query=f"{company_name} hiring jobs 2025 2026 site:linkedin.com OR site:indeed.com",
            max_results=3,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:1200]
    except Exception as e:
        return f"Could not fetch job postings: {e}"


def find_tech_stack(company_name: str, company_website: Optional[str] = None) -> str:
    """Find company's tech stack via search."""
    if not company_name or not company_name.strip():
        return "No company name available to search tech stack for."
    try:
        results = _tavily().search(
            query=f"{company_name} tech stack technology infrastructure engineering blog",
            max_results=2,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:800]
    except Exception as e:
        return f"Could not fetch tech stack: {e}"


# ---------------------------------------------------------------------------
# MCP-facing wrappers
# ---------------------------------------------------------------------------
def scrape_or_search_profile(linkedin_url: str) -> dict:
    """
    MCP tool entry point. `scrape_linkedin_profile` above already implements
    exactly this "try Proxycurl, else search-and-extract" behavior, so this
    is a thin, clearly-named alias for external MCP clients.
    """
    return scrape_linkedin_profile(linkedin_url)


def generate_outreach_email(profile_data: dict, sender_name: str, sender_company: str) -> str:
    """
    MCP tool entry point. Drafts a personalized cold email from profile data
    alone. Unlike agent.graph.node_email, this has no company_news /
    job_postings context (an MCP caller may not have run research first) and
    takes sender_name/sender_company as explicit args instead of reading
    SENDER_NAME from the environment, since an external MCP client has no
    reason to share this process's env vars.
    """
    # Local import to avoid a circular import: agent.llm imports
    # TOOL_SCHEMAS/execute_tool from agent.tools, so agent.tools importing
    # agent.llm at module load time would deadlock the import graph.
    from agent.llm import chat

    profile_data = profile_data or {}
    name = profile_data.get("name") or "there"
    first_name = name.split()[0] if name else "there"
    title = profile_data.get("title", "")
    company = profile_data.get("company") or ""
    summary = profile_data.get("summary") or ""

    company_line = f"at {company}" if company else "(no company on file - do not invent one)"

    prompt = f"""Write a hyper-personalized B2B cold email to {name}, {title} {company_line}.

Profile summary: {summary}

Sender: {sender_name}, from {sender_company}

Rules:
- Subject line referencing something specific about the recipient
- Address them as {first_name} (first name only)
- STRICTLY under 150 words
- Professional tone, not salesy
- Sign off with exactly this name: {sender_name} - never use a bracketed placeholder
- Simple, single call to action

Return ONLY the email with Subject: on the first line."""

    return chat(
        messages=[{"role": "user", "content": prompt}],
        system="You are an expert B2B sales copywriter. Write emails that get replies.",
    )


# Tool schemas for LLM tool-calling
TOOL_SCHEMAS = [
    {
        "name": "scrape_linkedin_profile",
        "description": "Scrape a LinkedIn profile to get name, title, company, and skills.",
        "input_schema": {
            "type": "object",
            "properties": {
                "linkedin_url": {"type": "string", "description": "Full LinkedIn profile URL"}
            },
            "required": ["linkedin_url"],
        },
    },
    {
        "name": "search_company_news",
        "description": "Search for latest news, funding rounds, or product launches for a company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "description": "Company name to search"}
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "analyze_job_postings",
        "description": "Analyze job postings to identify company pain points and hiring signals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "description": "Company name"}
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "find_tech_stack",
        "description": "Find the technology stack a company uses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "description": "Company name"},
                "company_website": {"type": "string", "description": "Optional company website URL"},
            },
            "required": ["company_name"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return string result."""
    if tool_name == "scrape_linkedin_profile":
        result = scrape_linkedin_profile(tool_input["linkedin_url"])
        return json.dumps(result)
    elif tool_name == "search_company_news":
        return search_company_news(tool_input["company_name"])
    elif tool_name == "analyze_job_postings":
        return analyze_job_postings(tool_input["company_name"])
    elif tool_name == "find_tech_stack":
        return find_tech_stack(
            tool_input["company_name"],
            tool_input.get("company_website"),
        )
    return f"Unknown tool: {tool_name}"