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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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