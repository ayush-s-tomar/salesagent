from fastapi import APIRouter
from pydantic import BaseModel
from agent.llm import chat

router = APIRouter()


class EmailRegenerateRequest(BaseModel):
    lead_name: str
    company: str
    title: str
    context: str = ""
    tone: str = "professional"


@router.post("/regenerate")
def regenerate_email(req: EmailRegenerateRequest):
    """Regenerate a cold email with a different tone."""
    prompt = f"""Write a {req.tone} B2B cold email to {req.lead_name}, {req.title} at {req.company}.
Context: {req.context}
Rules: Under 150 words, specific opener, one clear CTA. Return Subject: on first line."""

    email = chat(
        [{"role": "user", "content": prompt}],
        system="You are an expert B2B sales copywriter.",
    )
    return {"email": email}
