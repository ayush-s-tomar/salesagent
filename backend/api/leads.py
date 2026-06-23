from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from memory.store import get_all_leads, get_lead, get_interactions

router = APIRouter()


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    stage: Optional[str] = None


@router.get("/")
def list_leads():
    return get_all_leads()


@router.get("/{lead_id}")
def get_lead_detail(lead_id: int):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    lead["interactions"] = get_interactions(lead_id)
    return lead
