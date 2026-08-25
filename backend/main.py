from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import time

from agent.graph import run_agent
from api.leads import router as leads_router
from api.deals import router as deals_router
from api.emails import router as emails_router
from memory.store import init_db

app = FastAPI(title="SalesAgent API", version="1.0.0")

# FIX (CORS blocked in browser despite allow_origins=["*"]):
# Per the CORS spec, browsers refuse to honor a wildcard Access-Control-
# Allow-Origin header when Access-Control-Allow-Credentials is also true —
# that combination is disallowed for security reasons (a wildcard + cookies/
# credentials would let any site read credentialed responses). Starlette's
# CORSMiddleware is spec-compliant here: when allow_credentials=True and
# allow_origins=["*"], it does NOT actually echo back a valid
# Access-Control-Allow-Origin header, so the browser silently blocks the
# request with "No 'Access-Control-Allow-Origin' header is present" — this
# is exactly the error seen when the Vercel-hosted frontend called this API.
#
# This project has no auth layer (see README Known Limitations) and makes
# plain fetch() calls with no cookies, so there's no actual need for
# allow_credentials=True. Setting it to False makes the wildcard origin
# valid again and unblocks every current and future frontend deployment
# (Vercel production + preview URLs, Render, local dev) with zero
# per-domain maintenance.
#
# If auth/cookies are added later, allow_credentials must be switched back
# to True AND allow_origins must become an explicit list of exact origins
# (wildcard is not permitted alongside credentials by any spec-compliant
# browser) — see commented example below.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- If/when auth or cookie-based sessions are added, replace the block
# above with something like this instead:
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://salesagent-theta.vercel.app",
#         "https://salesagent-frontend-jwar.onrender.com",
#         "http://localhost:3000",
#     ],
#     allow_origin_regex=r"https://salesagent.*\.vercel\.app",  # Vercel preview URLs
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(deals_router, prefix="/api/deals", tags=["Deals"])
app.include_router(emails_router, prefix="/api/emails", tags=["Emails"])


class AgentRequest(BaseModel):
    linkedin_url: Optional[str] = None
    message: Optional[str] = None
    lead_id: Optional[int] = None


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "SalesAgent API running"}


# FIX: /api/agent/run had no rate limiting at all. This project's Groq/
# Tavily/Proxycurl API keys are single shared accounts (see README Known
# Limitations) with hard token/request caps — one visitor double-clicking
# "Run Agent," or anyone scripting requests directly against this public
# endpoint (bypassing the frontend entirely, as can be done with a plain
# curl call), could burn through the shared quota and 429 the agent for
# every other visitor. A lightweight in-memory per-IP limiter is enough to
# stop accidental double-submits and casual abuse without adding an auth
# layer or external dependency — it does NOT protect against a
# determined attacker spoofing IPs, but that's out of scope for a portfolio
# demo with no sensitive data behind it.
#
# In-memory means this resets on every deploy/restart and does not share
# state across multiple server processes/workers — acceptable here since
# render.yaml runs WEB_CONCURRENCY=1 (single process). If this ever moves
# to multiple workers or instances, replace with a shared store (Redis) or
# a proper rate-limiting middleware/service instead of scaling this dict.
_rate_limit_window_seconds = 30
_rate_limit_store: dict[str, float] = {}  # client_ip -> last_request_timestamp


def _get_client_ip(request: Request) -> str:
    """Resolve the real visitor IP behind Render + Cloudflare.

    request.client.host sees whoever connects directly to this process —
    behind Render's proxy (itself behind Cloudflare), that's Render's
    internal load-balancer IP, not the visitor, and it can vary per
    request. That's why the rate limiter below never triggered: every
    call looked like a "new" IP even from the same visitor within the
    same 30s window.

    CF-Connecting-IP is set by Cloudflare itself on every request that
    passes through it and can't be spoofed by an external caller on this
    path (Cloudflare overwrites it before forwarding), so it's checked
    first. X-Forwarded-For is a fallback for local/non-Cloudflare setups
    and IS spoofable by a direct caller — an accepted limitation given
    this endpoint's abuse-protection scope is "stop accidental double-
    submits and casual scripting," not "defend against a determined
    attacker."
    """
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()

    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str) -> Optional[float]:
    """Returns seconds remaining until the client may retry, or None if
    the request is allowed (and records this request's timestamp)."""
    now = time.monotonic()
    last = _rate_limit_store.get(client_ip)
    if last is not None:
        elapsed = now - last
        if elapsed < _rate_limit_window_seconds:
            return round(_rate_limit_window_seconds - elapsed, 1)
    _rate_limit_store[client_ip] = now
    return None


@app.post("/api/agent/run")
async def run_sales_agent(req: AgentRequest, request: Request):
    """Run the sales agent on a LinkedIn URL or natural language command."""
    if not req.linkedin_url and not req.message:
        raise HTTPException(400, "Provide linkedin_url or message")

    client_ip = _get_client_ip(request)
    retry_after = _check_rate_limit(client_ip)
    if retry_after is not None:
        raise HTTPException(
            429,
            f"Please wait {retry_after}s before running the agent again. "
            "This limit protects the shared demo API quota.",
        )

    async def event_stream():
        # FIX: previously, if run_agent() (or anything inside the graph)
        # raised, the generator just died mid-stream with no event — the
        # frontend would sit on its last "running" state forever with no
        # error shown. Now a failure is surfaced as a proper SSE event.
        try:
            async for event in run_agent(
                linkedin_url=req.linkedin_url,
                message=req.message,
                lead_id=req.lead_id,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'status': 'error', 'msg': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/health")
def health():
    return {"status": "ok"}