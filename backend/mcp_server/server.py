from mcp.server.fastmcp import FastMCP
from agent.tools import scrape_or_search_profile, generate_outreach_email

mcp = FastMCP("sales-agent")

@mcp.tool()
def get_profile(linkedin_url: str) -> dict:
    """Fetch and extract a LinkedIn profile, with search fallback."""
    return scrape_or_search_profile(linkedin_url)

@mcp.tool()
def draft_email(profile_data: dict, sender_name: str, sender_company: str) -> str:
    """Generate a personalized outreach email for a lead."""
    return generate_outreach_email(profile_data, sender_name, sender_company)

if __name__ == "__main__":
    mcp.run()