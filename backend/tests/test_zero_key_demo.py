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


@pytest.mark.asyncio
async def test_adversarial_surge_with_toggled_live_mode_resilience():
    """
    Quality Audit Test: Verifies that even if live mode is toggled with no API credentials,
    the adversarial surge test NEVER throws an uncaught error and correctly triggers HITL hold.
    """
    orchestrator = NexusOrchestrator()
    # Simulate user toggling to Live Mode without keys
    orchestrator.channel3_provider.set_demo_mode(False)
    orchestrator.paypal_provider.set_demo_mode(False)

    mandate = orchestrator.create_mandate({
        "title": "NVIDIA H100 GPU Cluster Procurement",
        "item_name": "NVIDIA H100 SXM5 80GB Server Node",
        "quantity": 100,
        "max_unit_price": 32000.0,
        "max_total_budget": 3200000.0,
        "target_categories": ["Networking Hardware", "Edge Infrastructure"],
    })

    session = await orchestrator.run_autonomous_negotiation(
        mandate_id=mandate.id,
        simulate_violation="PRICE_SPIKE",
    )
    assert session.status.value == "HITL_HOLD"
    assert "UNIT_PRICE_EXCEEDED" in session.hitl_reason or "violated" in session.hitl_reason
    assert session.hitl_flagged_proposal is not None
    assert session.hitl_flagged_proposal.proposed_unit_price > mandate.max_unit_price


@pytest.mark.asyncio
async def test_api_full_lifecycle_demo_endpoint_hitl_surge():
    """
    Quality Audit Test: Tests the FastAPI /api/demo/run-full-lifecycle endpoint
    with simulate_hitl_hold=True and simulate_hitl_hold=False.
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test 1: Adversarial Surge Injection
        surge_resp = await ac.post("/api/demo/run-full-lifecycle", json={
            "item_name": "NVIDIA H100 SXM5 80GB Server Node",
            "quantity": 100,
            "max_unit_price": 32000.0,
            "max_total_budget": 3200000.0,
            "simulate_hitl_hold": True,
        })
        assert surge_resp.status_code == 200
        data = surge_resp.json()
        assert data["lifecycle_status"] == "HITL_HOLD_TRIGGERED"
        assert data["session"]["status"] == "HITL_HOLD"
        assert data["escrow_order"] is None
        assert "PolicyEngine trapped adversarial surge" in data["message"]

        # Test 2: Happy Path Settlement
        happy_resp = await ac.post("/api/demo/run-full-lifecycle", json={
            "item_name": "OptixFabric 48-Port L3 Spine Switch",
            "quantity": 20,
            "max_unit_price": 2850.0,
            "max_total_budget": 57000.0,
            "simulate_hitl_hold": False,
        })
        assert happy_resp.status_code == 200
        happy_data = happy_resp.json()
        assert happy_data["lifecycle_status"] == "COMPLETED_SETTLED"
        assert happy_data["escrow_order"]["status"] == "COMPLETED"
        assert happy_data["evidence_bundle"]["tamper_evident_valid"] is True


@pytest.mark.asyncio
async def test_sqlite_persistence_continuity_across_restarts(tmp_path):
    """
    Quality Audit Test: Verifies SQLite persistence continuity.
    Simulates a full backend restart/reload and ensures that newly created
    mandates, negotiations, escrow orders, and evidence bundles survive intact.
    """
    db_file = str(tmp_path / "test_persistence.db")

    # Instance 1: Create transaction
    orch1 = NexusOrchestrator(db_path=db_file)
    mandate = orch1.create_mandate({
        "title": "Persistent Datacenter Order",
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 25,
        "max_unit_price": 1200.0,
        "max_total_budget": 30000.0,
    })
    session = await orch1.run_autonomous_negotiation(mandate.id)
    order, bundle = await orch1.finalize_agreement_and_authorize_escrow(session.session_id)
    order_id = order.order_id
    bundle_id = bundle.bundle_id

    # Advance Milestone 2
    updated_order, _ = await orch1.advance_to_shipment_milestone(order_id)
    assert updated_order.status == EscrowStatus.IN_TRANSIT

    # Instance 2: Simulate full server reboot/reload
    orch2 = NexusOrchestrator(db_path=db_file)
    assert mandate.id in orch2.mandates
    assert session.session_id in orch2.sessions
    assert order_id in orch2.orders
    assert bundle_id in orch2.bundles

    reloaded_order = orch2.orders[order_id]
    assert reloaded_order.status == EscrowStatus.IN_TRANSIT
    assert reloaded_order.quantity == 25
    assert reloaded_order.milestones[1].status == MilestoneStepStatus.COMPLETED

    reloaded_bundle = orch2.bundles[bundle_id]
    assert reloaded_bundle.verify_integrity() is True
