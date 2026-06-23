from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from memory.store import get_all_deals, update_deal_stage

router = APIRouter()

STAGES = ["Lead", "Contacted", "Qualified", "Proposal", "Closed Won", "Closed Lost"]


class StageUpdate(BaseModel):
    stage: str


@router.get("/")
def list_deals():
    return get_all_deals()


@router.patch("/{deal_id}/stage")
def move_deal(deal_id: int, body: StageUpdate):
    if body.stage not in STAGES:
        raise HTTPException(400, f"Invalid stage. Choose from: {STAGES}")
    update_deal_stage(deal_id, body.stage)
    return {"status": "updated", "deal_id": deal_id, "stage": body.stage}


@router.get("/stages")
def get_stages():
    return STAGES
