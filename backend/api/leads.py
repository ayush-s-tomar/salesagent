from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from memory.store import get_all_leads, get_lead, get_interactions, update_lead

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


# FIX: LeadUpdate was defined but never used anywhere — there was no way to
# actually edit a lead (e.g. move it to a new stage, fix a name) via the API.
# This wires it up to memory.store.update_lead.
@router.patch("/{lead_id}")
def patch_lead(lead_id: int, payload: LeadUpdate):
    existing = get_lead(lead_id)
    if not existing:
        raise HTTPException(404, "Lead not found")
    updated = update_lead(lead_id, **payload.model_dump(exclude_unset=True))
    return updated