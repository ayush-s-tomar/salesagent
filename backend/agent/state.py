from typing import TypedDict, Optional, List, Any


class AgentState(TypedDict):
    # Input
    linkedin_url: Optional[str]
    message: Optional[str]
    lead_id: Optional[int]

    # Gathered data
    profile: Optional[dict]         # LinkedIn profile data
    company_news: Optional[str]     # Latest company news
    job_postings: Optional[str]     # Pain points from job ads
    tech_stack: Optional[str]       # Company tech stack
    lead_score: Optional[float]     # ML score 0-100
    sentiment: Optional[str]        # Past email sentiment

    # Outputs
    email_draft: Optional[str]      # Generated cold email
    deal_id: Optional[int]          # Created/updated deal
    followup_date: Optional[str]    # Scheduled follow-up

    # Trace (for live UI)
    trace: List[dict]
    errors: List[str]
