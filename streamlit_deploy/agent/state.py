from typing import TypedDict, Optional, List, Any


class AgentState(TypedDict):
    linkedin_url: Optional[str]
    message: Optional[str]
    lead_id: Optional[int]

    profile: Optional[dict]
    company_news: Optional[str]
    job_postings: Optional[str]
    tech_stack: Optional[str]
    lead_score: Optional[float]
    sentiment: Optional[str]

    email_draft: Optional[str]
    deal_id: Optional[int]
    followup_date: Optional[str]

    trace: List[dict]
    errors: List[str]
