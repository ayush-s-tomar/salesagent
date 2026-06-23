import os
import json
import httpx
from typing import Optional
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))


def scrape_linkedin_profile(linkedin_url: str) -> dict:
    """
    Scrape public LinkedIn profile data.
    Uses Proxycurl API if key is set, otherwise returns mock data for dev.
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
                }
        except Exception as e:
            print(f"Proxycurl error: {e}")

    # Fallback: extract name from URL slug
    slug = linkedin_url.rstrip("/").split("/")[-1].replace("-", " ").title()
    return {
        "name": slug,
        "title": "Professional",
        "company": "Unknown Company",
        "location": "",
        "summary": "",
        "skills": [],
        "linkedin_url": linkedin_url,
    }


def search_company_news(company_name: str) -> str:
    """Search for latest company news, funding, product launches."""
    try:
        results = tavily.search(
            query=f"{company_name} latest news funding product launch 2024 2025",
            max_results=3,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:1500]
    except Exception as e:
        return f"Could not fetch news: {e}"


def analyze_job_postings(company_name: str) -> str:
    """Find pain points by analyzing what roles the company is hiring for."""
    try:
        results = tavily.search(
            query=f"{company_name} hiring jobs 2024 2025 site:linkedin.com OR site:indeed.com",
            max_results=3,
        )
        snippets = [r.get("content", "") for r in results.get("results", [])]
        return " ".join(snippets)[:1200]
    except Exception as e:
        return f"Could not fetch job postings: {e}"


def find_tech_stack(company_name: str, company_website: Optional[str] = None) -> str:
    """Find company's tech stack via search."""
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
