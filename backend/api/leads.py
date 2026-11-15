import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from memory.store import get_all_leads, get_lead, get_interactions, update_lead, log_interaction

router = APIRouter()

MAX_DRAFT_CHARS = 5000


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    stage: Optional[str] = None
    email_draft: Optional[str] = None


@router.get("/")
def list_leads():
    return get_all_leads()


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
CSV_COLUMNS = [
    "id", "name", "title", "company", "location", "linkedin_url",
    "email", "score", "stage", "created_at", "email_draft",
]


def _csv_safe(value):
    """Neutralise spreadsheet formulas: names and titles come from search results."""
    if value is None:
        return ""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


# Defined before "/{lead_id}" so "export.csv" is not parsed as a lead id.
@router.get("/export.csv")
def export_leads_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for row in get_all_leads():
        writer.writerow([_csv_safe(row.get(column)) for column in CSV_COLUMNS])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads.csv"'},
    )


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
    changes = payload.model_dump(exclude_unset=True)
    draft = changes.get("email_draft")
    if draft is not None:
        if not draft.strip():
            raise HTTPException(400, "Email draft cannot be empty.")
        if len(draft) > MAX_DRAFT_CHARS:
            raise HTTPException(400, f"Email draft is too long (max {MAX_DRAFT_CHARS} characters).")
    updated = update_lead(lead_id, **changes)
    if draft is not None:
        log_interaction(lead_id, "email_edited", draft)
    return updated