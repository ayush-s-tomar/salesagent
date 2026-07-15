# FIX: this is a standalone entry point (run directly, not imported by
# main.py), so unlike main.py (`from dotenv import load_dotenv; load_dotenv()`)
# and streamlit_app.py (reads st.secrets into os.environ), nothing here ever
# loaded your .env file. It only worked at all if GROQ_API_KEY/TAVILY_API_KEY
# happened to already be exported in the shell. Loading .env explicitly here
# makes `python mcp_server/server.py` work the same way regardless of how
# it's launched (terminal, Claude Desktop config, etc).
from dotenv import load_dotenv
load_dotenv()

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