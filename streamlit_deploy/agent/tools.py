import os
import json
import httpx
from typing import Optional
from tavily import TavilyClient
from groq import Groq

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
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
                    "location": data.get("city", ""),
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


def _search_based_profile(linkedin_url: str, fallback_name: str) -> dict:
    """
    No Proxycurl key: use Tavily to search for this specific LinkedIn URL,
    then ask an LLM to extract name/title/company/location from the
    snippets. Falls back to slug-only data if search returns nothing
    useful, but never silently returns identical blank data for every
    profile the way the old fallback did.
    """
    try:
        results = tavily.search(
            query=f'"{linkedin_url}" OR "{fallback_name}" linkedin profile title company',
            max_results=5,
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
        resp = groq_client.chat.completions.create(
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
        "location": extracted.get("location") or "",
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
        results = tavily.search(
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
        results = tavily.search(
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
        results = tavily.search(
            query=f"{company_name} tech stack technology infrastructure engineering blog",
            max_results=2,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:800]
    except Exception as e:
        return f"Could not fetch tech stack: {e}"


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
