"""
NexusCommerce AI - Agent Negotiation API
Exposes multi-agent negotiation, PolicyEngine verification, HITL hold handling,
and human supervisor overrides.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.negotiation import NegotiationSession, FinalAgreement

router = APIRouter(prefix="/api/negotiate", tags=["Agent Negotiation"])


def get_orchestrator():
    from app.main import orchestrator
    return orchestrator


class StartNegotiationRequest(BaseModel):
    mandate_id: str
    catalog_item_id: Optional[str] = None
    simulate_violation: Optional[str] = None  # None | "PRICE_SPIKE" | "MALFORMED" | "QUANTITY_MUTATION"
    max_rounds: int = 4


class HitlOverrideRequest(BaseModel):
    session_id: str
    supervisor_notes: str = "Authorized by Human Procurement Supervisor after manual vendor review."


@router.post("/start", response_model=NegotiationSession)
async def start_negotiation(req: StartNegotiationRequest, orchestrator=Depends(get_orchestrator)):
    try:
        session = await orchestrator.run_autonomous_negotiation(
            mandate_id=req.mandate_id,
            catalog_item_id=req.catalog_item_id,
            simulate_violation=req.simulate_violation,
            max_rounds=req.max_rounds,
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/hitl-override", response_model=FinalAgreement)
async def hitl_override(req: HitlOverrideRequest, orchestrator=Depends(get_orchestrator)):
    try:
        agreement = orchestrator.handle_hitl_supervisor_override(
            session_id=req.session_id,
            supervisor_notes=req.supervisor_notes,
        )
        return agreement
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[NegotiationSession])
async def list_sessions(orchestrator=Depends(get_orchestrator)):
    return list(orchestrator.sessions.values())


@router.get("/sessions/{session_id}", response_model=NegotiationSession)
async def get_session(session_id: str, orchestrator=Depends(get_orchestrator)):
    session = orchestrator.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session
