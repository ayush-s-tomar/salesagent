from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

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


@app.post("/api/agent/run")
async def run_sales_agent(req: AgentRequest):
    """Run the sales agent on a LinkedIn URL or natural language command."""
    if not req.linkedin_url and not req.message:
        raise HTTPException(400, "Provide linkedin_url or message")

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