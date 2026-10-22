import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agent.graph import _validate_email
from agent.llm import chat, DailyQuotaExceededError

router = APIRouter()

ALLOWED_TONES = {"professional", "friendly", "concise", "direct"}
_WINDOW_SECONDS = 10
_last_call: dict = {}  # client key -> last request time (in-memory, resets on restart)


class EmailRegenerateRequest(BaseModel):
    lead_name: str
    company: str
    title: str
    context: str = ""  # the existing draft to rewrite
    tone: str = "professional"


def _client_key(request: Request) -> str:
    cf = request.headers.get("CF-Connecting-IP")
    if cf:
        return cf.strip()
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/regenerate")
def regenerate_email(req: EmailRegenerateRequest, request: Request):
    """Rewrite an existing draft in a different tone, using only facts already in it."""
    if not req.context.strip():
        raise HTTPException(400, "An existing draft is required in 'context'.")

    key = _client_key(request)
    now = time.monotonic()
    last = _last_call.get(key)
    if last is not None and now - last < _WINDOW_SECONDS:
        wait = round(_WINDOW_SECONDS - (now - last), 1)
        raise HTTPException(429, f"Please wait {wait}s before rewriting again.")
    _last_call[key] = now

    tone = req.tone.strip().lower()
    if tone not in ALLOWED_TONES:
        tone = "professional"

    prompt = f"""Rewrite the cold email below in a {tone} tone.
Recipient: {req.lead_name}, {req.title} at {req.company}.

Rules:
- Use ONLY facts, names and numbers that already appear in the email below.
  Do not add new facts, numbers, dates or product claims.
- Keep one clear call to action and the same sign-off.
- Under 150 words. Keep a Subject: line first. Separate paragraphs with a blank line.

Email:
---
{req.context}
---

Return ONLY the rewritten email."""

    try:
        email = chat(
            [{"role": "user", "content": prompt}],
            system="You are an expert B2B sales copywriter. You never invent facts.",
        )
    except DailyQuotaExceededError:
        raise HTTPException(503, "The shared daily AI quota is exhausted. Please try again later.")
    except Exception:
        raise HTTPException(502, "The rewrite failed. Please try again.")

    email = (email or "").strip()
    if not email or _validate_email(email, req.context):
        return {
            "email": req.context,
            "note": "The rewrite broke the guardrails (new facts or filler), so the original is shown.",
        }
    return {"email": email}