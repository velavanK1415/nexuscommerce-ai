"""
NexusCommerce AI - PayPal Webhook Handlers
Supports Webhooks First with Polling Fallback.
Handles:
- CHECKOUT.ORDER.APPROVED
- PAYMENT.AUTHORIZATION.CREATED
- PAYMENT.CAPTURE.COMPLETED
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Depends
import logging

from app.models.escrow import EscrowStatus, MilestoneStepStatus
from app.models.mandate import MandateStatus
from app.core.evidence_bundle import EvidenceBundleManager

logger = logging.getLogger("nexus.webhooks")
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

# Webhook event ledger
received_events: List[Dict[str, Any]] = []


def get_orchestrator():
    from app.main import orchestrator
    return orchestrator


def find_matching_order(resource: Dict[str, Any], payload: Dict[str, Any], orders: Dict[str, Any]):
    res_id = resource.get("id")
    custom_id = resource.get("custom_id") or payload.get("custom_id")
    related = resource.get("supplementary_data", {}).get("related_ids", {})
    parent_payment = resource.get("parent_payment")
    auth_id = related.get("authorization_id") or parent_payment
    paypal_order_id = related.get("order_id")

    # Priority 1: Match by exact custom_id (order_id or mandate_id)
    if custom_id:
        for order in orders.values():
            if order.order_id == custom_id or order.mandate_id == custom_id:
                return order

    # Priority 2: Match by unique PayPal authorization ID
    if auth_id:
        for order in orders.values():
            if order.paypal_authorization_id == auth_id:
                return order

    # Priority 3: Match by PayPal order ID
    if paypal_order_id:
        for order in orders.values():
            if order.paypal_order_id == paypal_order_id:
                return order

    # Priority 4: Match by resource ID
    if res_id:
        for order in orders.values():
            if (
                order.order_id == res_id
                or order.paypal_order_id == res_id
                or order.paypal_authorization_id == res_id
                or order.paypal_capture_id == res_id
            ):
                return order
    return None


@router.post("/paypal")
async def receive_paypal_webhook(payload: Dict[str, Any], orchestrator=Depends(get_orchestrator)):
    """
    Standard PayPal Webhook ingestion endpoint.
    Handles:
    - CHECKOUT.ORDER.APPROVED
    - PAYMENT.AUTHORIZATION.CREATED
    - PAYMENT.CAPTURE.COMPLETED
    """
    event_type = payload.get("event_type")
    resource = payload.get("resource", {})
    resource_id = resource.get("id")

    event_record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "event_id": payload.get("id"),
        "resource_id": resource_id,
        "payload": payload,
        "handled": False,
    }
    received_events.append(event_record)
    logger.info(f"Received PayPal Webhook: {event_type} for resource: {resource_id}")

    matched_order = find_matching_order(resource, payload, orchestrator.orders)

    # Process events
    if event_type == "CHECKOUT.ORDER.APPROVED" and matched_order:
        matched_order.status = EscrowStatus.FUNDS_AUTHORIZED
        matched_order.milestones[0].status = MilestoneStepStatus.COMPLETED
        matched_order.milestones[0].completed_at = datetime.now(timezone.utc).isoformat()
        if resource_id and not matched_order.paypal_order_id:
            matched_order.paypal_order_id = resource_id
        if matched_order.milestones[1].status == MilestoneStepStatus.PENDING:
            matched_order.milestones[1].status = MilestoneStepStatus.IN_PROGRESS
        matched_order.updated_at = datetime.now(timezone.utc).isoformat()
        event_record["handled"] = True

    elif event_type == "PAYMENT.AUTHORIZATION.CREATED" and matched_order:
        matched_order.status = EscrowStatus.FUNDS_AUTHORIZED
        matched_order.paypal_authorization_id = resource_id or matched_order.paypal_authorization_id
        matched_order.milestones[0].status = MilestoneStepStatus.COMPLETED
        matched_order.milestones[0].completed_at = datetime.now(timezone.utc).isoformat()
        matched_order.milestones[0].paypal_reference_id = matched_order.paypal_authorization_id
        if matched_order.milestones[1].status == MilestoneStepStatus.PENDING:
            matched_order.milestones[1].status = MilestoneStepStatus.IN_PROGRESS
        matched_order.updated_at = datetime.now(timezone.utc).isoformat()
        event_record["handled"] = True

    elif event_type == "PAYMENT.CAPTURE.COMPLETED" and matched_order:
        capture_id = resource_id or f"CAP-{int(datetime.now(timezone.utc).timestamp())}"
        matched_order.status = EscrowStatus.COMPLETED
        matched_order.paypal_capture_id = capture_id
        matched_order.carrier_status = "DELIVERED"
        matched_order.milestones[2].status = MilestoneStepStatus.COMPLETED
        matched_order.milestones[2].completed_at = datetime.now(timezone.utc).isoformat()
        matched_order.milestones[2].released_amount = matched_order.total_amount
        matched_order.milestones[2].paypal_reference_id = capture_id
        matched_order.updated_at = datetime.now(timezone.utc).isoformat()

        # Update Mandate status
        mandate = orchestrator.mandates.get(matched_order.mandate_id)
        if mandate:
            mandate.status = MandateStatus.COMPLETED

        # Attach capture proof to Evidence Bundle
        bundle = orchestrator.bundles.get(matched_order.evidence_bundle_id or "")
        if bundle:
            fee = round(matched_order.total_amount * 0.029 + 0.30, 2)
            EvidenceBundleManager.attach_paypal_capture_receipt(
                bundle=bundle,
                capture_id=capture_id,
                amount_captured=matched_order.total_amount,
                currency=matched_order.currency,
                fee=fee,
            )

        event_record["handled"] = True

    return {"status": "SUCCESS", "event_type": event_type, "handled": event_record["handled"]}


@router.post("/simulate")
async def simulate_webhook(
    event_type: str,
    order_id: str,
    orchestrator=Depends(get_orchestrator),
):
    """
    Test harness for judges to trigger simulated PayPal webhooks directly.
    """
    order = orchestrator.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    is_capture = "CAPTURE" in event_type
    is_order = "ORDER" in event_type

    res_id = (
        order.paypal_order_id
        if is_order
        else (f"CAP-WH-{order.order_id[-6:]}" if is_capture else (order.paypal_authorization_id or "AUTH-SIM-001"))
    )

    simulated_payload = {
        "id": f"WH-SIM-{int(datetime.now(timezone.utc).timestamp())}",
        "create_time": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "event_version": "1.0",
        "resource_type": "checkout-order" if is_order else ("payment-capture" if is_capture else "payment-authorization"),
        "resource": {
            "id": res_id,
            "custom_id": order.order_id,
            "status": "COMPLETED" if is_capture else "APPROVED",
            "amount": {"currency_code": order.currency, "value": f"{order.total_amount:.2f}"},
            "parent_payment": order.paypal_authorization_id,
            "supplementary_data": {
                "related_ids": {
                    "order_id": order.paypal_order_id,
                    "authorization_id": order.paypal_authorization_id,
                }
            },
        },
    }

    res = await receive_paypal_webhook(simulated_payload, orchestrator)
    return {"message": f"Simulated webhook {event_type} dispatched successfully.", "result": res}


@router.get("/events")
async def list_received_events():
    return {"total_events": len(received_events), "events": received_events[-20:]}
