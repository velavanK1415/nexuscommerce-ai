"""
NexusCommerce AI - Escrow Management API
Milestone-based Escrow Settlement on PayPal.
Enforces the invariant: only PolicyEngine triggers PayPal API operations.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.escrow import EscrowOrder

router = APIRouter(prefix="/api/escrow", tags=["Milestone Escrow"])


def get_orchestrator():
    from app.main import orchestrator
    return orchestrator


class AuthorizeEscrowRequest(BaseModel):
    session_id: str


class ShipmentProofRequest(BaseModel):
    carrier_name: str = "FedEx Priority Freight"
    tracking_number: Optional[str] = None


@router.post("/authorize", response_model=Dict[str, Any])
async def authorize_escrow(req: AuthorizeEscrowRequest, orchestrator=Depends(get_orchestrator)):
    try:
        order, bundle = await orchestrator.finalize_agreement_and_authorize_escrow(req.session_id)
        return {
            "order": order.model_dump(),
            "evidence_bundle_id": bundle.bundle_id,
            "message": "29-day authorization hold placed via PayPal Orders v2. Milestone 1 Complete.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/advance-shipment", response_model=Dict[str, Any])
async def advance_to_shipment(
    order_id: str,
    req: ShipmentProofRequest,
    orchestrator=Depends(get_orchestrator),
):
    try:
        order, bundle = await orchestrator.advance_to_shipment_milestone(
            order_id=order_id,
            carrier_name=req.carrier_name,
            tracking_number=req.tracking_number,
        )
        return {
            "order": order.model_dump(),
            "carrier_tracking": order.tracking_number,
            "carrier_status": order.carrier_status,
            "message": "Milestone 2 Verified: Carrier shipment proof ingested into Evidence Bundle.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/advance-delivery", response_model=Dict[str, Any])
async def advance_to_delivery_and_capture(order_id: str, orchestrator=Depends(get_orchestrator)):
    try:
        order, bundle = await orchestrator.advance_to_delivery_and_capture(order_id)
        return {
            "order": order.model_dump(),
            "paypal_capture_id": order.paypal_capture_id,
            "status": order.status.value,
            "message": "Milestone 3 Released: Delivery verified, final 70% PayPal capture completed and settled.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_model=List[EscrowOrder])
async def list_orders(orchestrator=Depends(get_orchestrator)):
    return list(orchestrator.orders.values())


@router.get("/orders/{order_id}", response_model=EscrowOrder)
async def get_order(order_id: str, orchestrator=Depends(get_orchestrator)):
    order = orchestrator.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order
