"""
NexusCommerce AI - Zero-Key Demo API
Allows judges and hackathon evaluators to run the full autonomous end-to-end lifecycle
without requiring any PayPal or sponsor credentials.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/demo", tags=["Zero-Key Demo Harness"])


def get_orchestrator():
    from app.main import orchestrator
    return orchestrator


class FullLifecycleRequest(BaseModel):
    item_name: str = "NexusEdge Pro 100G Modular Edge Router"
    quantity: int = 50
    max_unit_price: float = 1200.0
    max_total_budget: float = 60000.0
    simulate_hitl_hold: bool = False


@router.post("/run-full-lifecycle")
async def run_full_lifecycle(req: FullLifecycleRequest, orchestrator=Depends(get_orchestrator)):
    """
    Executes the entire NexusCommerce AI pipeline:
    1. Mandate Creation & Digital Signature
    2. Channel3 Supplier Discovery
    3. Multi-Agent Negotiation (ProcureBot vs VendorBot)
    4. PolicyEngine Deterministic Guarding
    5. Escrow Authorization (PayPal REST API v2)
    6. Evidence Bundle Sealing
    7. Carrier Shipment Proof Ingestion
    8. Delivery Verification & Escrow Release Capture
    """
    # 1. Mandate
    mandate_data = {
        "title": f"Autonomous Sourcing: {req.item_name}",
        "item_name": req.item_name,
        "quantity": req.quantity,
        "max_unit_price": req.max_unit_price,
        "max_total_budget": req.max_total_budget,
        "target_categories": ["Networking Hardware", "Edge Infrastructure"],
    }
    mandate = orchestrator.create_mandate(mandate_data)

    # 2 & 3. Negotiation
    violation = "PRICE_SPIKE" if req.simulate_hitl_hold else None
    session = await orchestrator.run_autonomous_negotiation(
        mandate_id=mandate.id,
        simulate_violation=violation,
    )

    if session.status.value == "HITL_HOLD":
        return {
            "lifecycle_status": "HITL_HOLD_TRIGGERED",
            "mandate": mandate.model_dump(),
            "session": session.model_dump(),
            "message": "PolicyEngine detected rule violation and placed order into Human-in-the-Loop review hold.",
        }

    # 4 & 5. PayPal Escrow Authorization & Evidence Bundle Sealing
    escrow_order, bundle = await orchestrator.finalize_agreement_and_authorize_escrow(session.session_id)

    # 6. Milestone 2: Carrier Shipment Proof
    escrow_order, bundle = await orchestrator.advance_to_shipment_milestone(
        order_id=escrow_order.order_id,
        carrier_name="FedEx Priority Freight",
    )

    # 7. Milestone 3: Delivery Verification & PayPal Capture
    escrow_order, bundle = await orchestrator.advance_to_delivery_and_capture(
        order_id=escrow_order.order_id,
    )

    return {
        "lifecycle_status": "COMPLETED_SETTLED",
        "mandate": mandate.model_dump(),
        "negotiation_session": session.model_dump(),
        "escrow_order": escrow_order.model_dump(),
        "evidence_bundle": bundle.model_dump(),
        "verification_result": {
            "root_sha256": bundle.bundle_root_hash,
            "tamper_evident_valid": bundle.tamper_evident_valid,
            "dispute_defense_grade": "A+",
            "mandate_diff": bundle.mandate_diff,
        },
    }


@router.post("/toggle-mode")
async def toggle_demo_mode(enabled: bool, orchestrator=Depends(get_orchestrator)):
    orchestrator.paypal_provider.set_demo_mode(enabled)
    orchestrator.channel3_provider.set_demo_mode(enabled)
    return {
        "demo_mode": enabled,
        "message": f"Zero-Key Demo Mode set to {enabled}",
    }


@router.get("/status")
async def get_demo_status(orchestrator=Depends(get_orchestrator)):
    return {
        "demo_mode_active": orchestrator.paypal_provider.is_demo_mode(),
        "channel3_demo_active": orchestrator.channel3_provider.is_demo_mode(),
        "total_mandates": len(orchestrator.mandates),
        "total_sessions": len(orchestrator.sessions),
        "total_escrow_orders": len(orchestrator.orders),
    }


@router.get("/catalog")
async def get_catalog(orchestrator=Depends(get_orchestrator)):
    items = await orchestrator.channel3_provider.search_catalog()
    return {"catalog": items}
