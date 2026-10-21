import pytest
from app.core.orchestrator import NexusOrchestrator
from app.core.polling_service import PollingFallbackService
from app.models.escrow import EscrowStatus, MilestoneStepStatus


@pytest.mark.asyncio
async def test_zero_key_full_lifecycle():
    orchestrator = NexusOrchestrator()
    assert orchestrator.paypal_provider.is_demo_mode() is True

    # 1. Create Mandate
    mandate = orchestrator.create_mandate({
        "title": "Autonomous Datacenter Switch Procurement",
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
        "target_categories": ["Networking Hardware"],
    })
    assert mandate.signature is not None

    # 2. Multi-Agent Negotiation
    session = await orchestrator.run_autonomous_negotiation(mandate_id=mandate.id)
    assert session.status.value == "AGREEMENT_REACHED"
    assert session.agreement is not None
    assert session.agreement.final_unit_price <= mandate.max_unit_price
    assert session.agreement.final_total <= mandate.max_total_budget
    assert len(session.proposals) >= 2

    # 3. PayPal Escrow Authorization via PolicyEngine
    order, bundle = await orchestrator.finalize_agreement_and_authorize_escrow(session.session_id)
    assert order.status == EscrowStatus.FUNDS_AUTHORIZED
    assert order.paypal_authorization_id is not None
    assert bundle.bundle_root_hash != ""

    # 4. Advance Carrier Shipment (Milestone 2)
    updated_order, bundle = await orchestrator.advance_to_shipment_milestone(
        order_id=order.order_id,
        carrier_name="FedEx Priority Freight",
    )
    assert updated_order.status == EscrowStatus.IN_TRANSIT
    assert updated_order.milestones[1].status == MilestoneStepStatus.COMPLETED

    # 5. Advance Delivery Verification & Capture (Milestone 3)
    completed_order, bundle = await orchestrator.advance_to_delivery_and_capture(
        order_id=order.order_id,
    )
    assert completed_order.status == EscrowStatus.COMPLETED
    assert completed_order.paypal_capture_id is not None
    assert bundle.paypal_capture_receipt is not None
    assert bundle.verify_integrity() is True


@pytest.mark.asyncio
async def test_zero_key_adversarial_hitl_hold():
    orchestrator = NexusOrchestrator()

    mandate = orchestrator.create_mandate({
        "title": "Adversarial Test Mandate",
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
        "target_categories": ["Networking Hardware"],
    })

    # Simulate adversarial price spike in negotiation
    session = await orchestrator.run_autonomous_negotiation(
        mandate_id=mandate.id,
        simulate_violation="PRICE_SPIKE",
    )
    # MUST be flagged into HITL hold by PolicyEngine!
    assert session.status.value == "HITL_HOLD"
    assert session.hitl_reason is not None
    assert "UNIT_PRICE_EXCEEDED" in session.hitl_reason or "violated" in session.hitl_reason

    # Human supervisor override
    agreement = orchestrator.handle_hitl_supervisor_override(
        session_id=session.session_id,
        supervisor_notes="Overridden with VP approval.",
    )
    assert agreement is not None
    assert session.status.value == "AGREEMENT_REACHED"


@pytest.mark.asyncio
async def test_polling_fallback_service():
    orchestrator = NexusOrchestrator()
    polling_service = PollingFallbackService(
        paypal_provider=orchestrator.paypal_provider,
        orders_store=orchestrator.orders,
    )

    # Create order in pending status
    mandate = orchestrator.create_mandate({
        "title": "Poll Test",
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 10,
        "max_unit_price": 1200.0,
        "max_total_budget": 12000.0,
    })
    session = await orchestrator.run_autonomous_negotiation(mandate.id)
    order, _ = await orchestrator.finalize_agreement_and_authorize_escrow(session.session_id)

    # Artificially set status back to AUTHORIZATION_PENDING to test polling reconciliation
    order.status = EscrowStatus.AUTHORIZATION_PENDING
    reconciled = await polling_service.reconcile_order(order.order_id)
    assert reconciled["reconciled"] is True
    assert order.status == EscrowStatus.FUNDS_AUTHORIZED
