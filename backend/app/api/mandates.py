"""
NexusCommerce AI - Mandate Management API
Handles creation, signing, validation, and listing of Procurement Mandates.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.models.mandate import ProcurementMandate, MandateCreateRequest

router = APIRouter(prefix="/api/mandates", tags=["Mandates"])


def get_orchestrator():
    from app.main import orchestrator
    return orchestrator


@router.post("", response_model=ProcurementMandate)
async def create_mandate(req: MandateCreateRequest, orchestrator=Depends(get_orchestrator)):
    mandate = orchestrator.create_mandate(req.model_dump())
    return mandate


@router.get("", response_model=List[ProcurementMandate])
async def list_mandates(orchestrator=Depends(get_orchestrator)):
    return list(orchestrator.mandates.values())


MANDATE_TEMPLATES = [
    {
        "id": "TEMPLATE-AI-GPUS",
        "title": "Autonomous Sourcing: AI Cluster GPUs (NVIDIA H100)",
        "item_name": "NVIDIA H100 SXM5 80GB Server Node",
        "category": "AI Compute Hardware",
        "target_categories": ["AI Compute Hardware", "Data Center Equipment"],
        "quantity": 100,
        "max_unit_price": 32000.0,
        "max_total_budget": 3200000.0,
        "quality_tier": "Enterprise",
        "lead_time_days": 14,
        "strictness": "Standard High-Value",
        "notes": "Requires Tier-1 enterprise warranty, authentic serial tracking, and two-step PayPal authorization hold with milestone captures.",
    },
    {
        "id": "TEMPLATE-DEFENSE-HW",
        "title": "Autonomous Sourcing: Strict Defense Tactical Gateways",
        "item_name": "Ruggedized Quantum-Resistant Tactical Gateway",
        "category": "Edge Infrastructure & Defense",
        "target_categories": ["Edge Infrastructure", "Networking Hardware"],
        "quantity": 50,
        "max_unit_price": 4500.0,
        "max_total_budget": 225000.0,
        "quality_tier": "Enterprise",
        "lead_time_days": 7,
        "strictness": "Strict Zero-Tolerance",
        "notes": "Strict 7-day delivery SLA. Zero tolerance for unverified carrier scan.",
    },
    {
        "id": "TEMPLATE-OFFICE-REFRESH",
        "title": "Autonomous Sourcing: Urgent Office Hardware Refresh",
        "item_name": "Nexus UltraWide 5K Thunderbolt Professional Displays",
        "category": "Enterprise Hardware",
        "target_categories": ["Enterprise Hardware"],
        "quantity": 200,
        "max_unit_price": 850.0,
        "max_total_budget": 170000.0,
        "quality_tier": "Standard",
        "lead_time_days": 5,
        "strictness": "Urgent SLA",
        "notes": "Fast commercial delivery. Bulk volume pricing expected.",
    },
]


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_mandate_templates():
    """
    Returns pre-filled mandate templates (AI Cluster GPUs, Strict Defense Hardware, Urgent Office Refresh)
    for 1-click evaluation and testing.
    """
    return MANDATE_TEMPLATES


@router.get("/{mandate_id}", response_model=ProcurementMandate)
async def get_mandate(mandate_id: str, orchestrator=Depends(get_orchestrator)):
    mandate = orchestrator.mandates.get(mandate_id)
    if not mandate:
        raise HTTPException(status_code=404, detail=f"Mandate {mandate_id} not found")
    return mandate
