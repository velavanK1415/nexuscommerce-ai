import pytest
from datetime import datetime, timezone, timedelta
import asyncio

from app.core.orchestrator import NexusOrchestrator
from app.core.policy_engine import PolicyEngine, PolicyDecisionType
from app.core.evidence_bundle import EvidenceBundleManager, compute_canonical_agreement_hash
from app.core.polling_service import PollingFallbackService
from app.models.mandate import ProcurementMandate, QualityTier
from app.models.negotiation import FinalAgreement, NegotiationSession, NegotiationProposal, ProposalSender
from app.models.escrow import EscrowStatus, MilestoneStepStatus
from app.providers.paypal_provider import PayPalProvider
from app.api.webhooks import receive_paypal_webhook


@pytest.fixture
def orchestrator():
    return NexusOrchestrator()


@pytest.mark.asyncio
async def test_policy_engine_rejects_unauthorized_paypal_escrow(orchestrator):
    """
    Test that PolicyEngine.authorize_paypal_escrow deterministically rejects
    any agreement that violates mandate boundaries or is expired.
    """
    now = datetime.now(timezone.utc)
    mandate = orchestrator.create_mandate({
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
    })

    # 1. Price ceiling breach without supervisor override
    unauthorized_agreement = FinalAgreement(
        agreement_id="AGR-UNAUTH-01",
        mandate_id=mandate.id,
        vendor_id="VEND-01",
        vendor_name="Rogue Supplier",
        item_name=mandate.item_name,
        final_unit_price=1350.0,  # Exceeds $1200
        final_quantity=40,
        final_total=54000.0,      # Under $60,000 budget, but unit price breached!
        lead_time_days=5,
        warranty_months=24,
        agreement_hash="hash1",
        buyer_signature=mandate.signature,  # Not supervisor override
    )

    with pytest.raises(ValueError) as excinfo:
        await orchestrator.policy_engine.authorize_paypal_escrow(mandate, unauthorized_agreement)
    assert "PRICE_CEILING_BREACH" in str(excinfo.value) or "INVARIANT VIOLATION" in str(excinfo.value)

    # 2. Quantity mismatch
    qty_mismatch = FinalAgreement(
        agreement_id="AGR-UNAUTH-02",
        mandate_id=mandate.id,
        vendor_id="VEND-01",
        vendor_name="Rogue Supplier",
        item_name=mandate.item_name,
        final_unit_price=1100.0,
        final_quantity=45,  # Mandate quantity is 50
        final_total=49500.0,
        lead_time_days=5,
        warranty_months=24,
        agreement_hash="hash2",
    )
    with pytest.raises(ValueError) as excinfo:
        await orchestrator.policy_engine.authorize_paypal_escrow(mandate, qty_mismatch)
    assert "QUANTITY_MISMATCH" in str(excinfo.value)

    # 3. Expired mandate rejection
    past = (now - timedelta(days=5)).isoformat()
    expired_mandate = ProcurementMandate(
        id="MAN-EXPIRED-TEST",
        buyer_id="BUYER-01",
        buyer_name="Apex Corp",
        buyer_email="buyer@apex.io",
        title="Expired Mandate",
        item_name="NexusEdge 100G",
        quantity=50,
        max_unit_price=1200.0,
        max_total_budget=60000.0,
        delivery_deadline=past,
        expiry_timestamp=past,
    )
    expired_mandate.sign()

    valid_agreement = FinalAgreement(
        agreement_id="AGR-VALID-TERMS",
        mandate_id=expired_mandate.id,
        vendor_id="VEND-01",
        vendor_name="Supplier",
        item_name=expired_mandate.item_name,
        final_unit_price=1100.0,
        final_quantity=50,
        final_total=55000.0,
        lead_time_days=5,
        warranty_months=24,
        agreement_hash="hash3",
    )
    with pytest.raises(ValueError) as excinfo:
        await orchestrator.policy_engine.authorize_paypal_escrow(expired_mandate, valid_agreement)
    assert "MANDATE_EXPIRED" in str(excinfo.value)


@pytest.mark.asyncio
async def test_multi_order_webhook_isolation(orchestrator):
    """
    Critical regression test:
    Verify that incoming webhooks for Order 2 do NOT mutate Order 1 even if both
    orders are in the IN_TRANSIT or AUTHORIZATION_PENDING state.
    """
    # Create Order 1
    m1 = orchestrator.create_mandate({"title": "Order 1 Mandate", "quantity": 10, "max_unit_price": 1200.0, "max_total_budget": 12000.0})
    s1 = await orchestrator.run_autonomous_negotiation(m1.id)
    assert s1.status.value == "AGREEMENT_REACHED"
    o1, b1 = await orchestrator.finalize_agreement_and_authorize_escrow(s1.session_id)
    o1, b1 = await orchestrator.advance_to_shipment_milestone(o1.order_id, carrier_name="FedEx")

    # Create Order 2
    m2 = orchestrator.create_mandate({"title": "Order 2 Mandate", "quantity": 20, "max_unit_price": 1200.0, "max_total_budget": 24000.0})
    s2 = await orchestrator.run_autonomous_negotiation(m2.id)
    assert s2.status.value == "AGREEMENT_REACHED"
    o2, b2 = await orchestrator.finalize_agreement_and_authorize_escrow(s2.session_id)
    o2, b2 = await orchestrator.advance_to_shipment_milestone(o2.order_id, carrier_name="UPS")

    assert o1.status == EscrowStatus.IN_TRANSIT
    assert o2.status == EscrowStatus.IN_TRANSIT
    assert o1.order_id != o2.order_id

    # Send PAYMENT.CAPTURE.COMPLETED targeting Order 2 ONLY
    capture_webhook = {
        "id": "WH-CAPTURE-ORD2",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAP-EXPLICIT-ORD2",
            "custom_id": o2.order_id,
            "status": "COMPLETED",
            "amount": {"currency_code": "USD", "value": f"{o2.total_amount:.2f}"},
            "parent_payment": o2.paypal_authorization_id,
        },
    }

    resp = await receive_paypal_webhook(capture_webhook, orchestrator)
    assert resp["handled"] is True

    # Order 2 must be COMPLETED
    assert o2.status == EscrowStatus.COMPLETED
    assert o2.paypal_capture_id == "CAP-EXPLICIT-ORD2"
    assert o2.milestones[2].status == MilestoneStepStatus.COMPLETED

    # CRITICAL INVARIANT: Order 1 must REMAIN IN_TRANSIT and NOT touched!
    assert o1.status == EscrowStatus.IN_TRANSIT
    assert o1.paypal_capture_id is None
    assert o1.milestones[2].status == MilestoneStepStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_webhook_custom_id_priority_over_stale_resource_id(orchestrator):
    """
    Ensure that when Order 1 already has paypal_capture_id='CAP-COMMON',
    an incoming webhook for Order 2 with resource.id='CAP-COMMON' and custom_id=o2.order_id
    correctly resolves to Order 2 via Priority 1 (custom_id) and updates Order 2.
    """
    m1 = orchestrator.create_mandate({"title": "Order A Mandate", "quantity": 10, "max_unit_price": 1200.0, "max_total_budget": 12000.0})
    s1 = await orchestrator.run_autonomous_negotiation(m1.id)
    assert s1.status.value == "AGREEMENT_REACHED"
    o1, _ = await orchestrator.finalize_agreement_and_authorize_escrow(s1.session_id)
    o1.status = EscrowStatus.COMPLETED
    o1.paypal_capture_id = "CAP-COMMON"

    m2 = orchestrator.create_mandate({"title": "Order B Mandate", "quantity": 10, "max_unit_price": 1200.0, "max_total_budget": 12000.0})
    s2 = await orchestrator.run_autonomous_negotiation(m2.id)
    assert s2.status.value == "AGREEMENT_REACHED"
    o2, _ = await orchestrator.finalize_agreement_and_authorize_escrow(s2.session_id)
    o2, _ = await orchestrator.advance_to_shipment_milestone(o2.order_id, carrier_name="FedEx")
    assert o2.status == EscrowStatus.IN_TRANSIT

    # Webhook carries the same capture ID as o1, but custom_id points to o2
    webhook = {
        "id": "WH-CAPTURE-DUP-ID",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAP-COMMON",
            "custom_id": o2.order_id,
            "status": "COMPLETED",
            "amount": {"currency_code": "USD", "value": f"{o2.total_amount:.2f}"},
            "parent_payment": o2.paypal_authorization_id,
        },
    }

    resp = await receive_paypal_webhook(webhook, orchestrator)
    assert resp["handled"] is True
    assert o2.status == EscrowStatus.COMPLETED
    assert o2.paypal_capture_id == "CAP-COMMON"


@pytest.mark.asyncio
async def test_polling_fallback_capture_and_milestone_activation(orchestrator):
    """
    Test polling service reconciling capture and milestone 2 activation.
    """
    polling_service = PollingFallbackService(
        paypal_provider=orchestrator.paypal_provider,
        orders_store=orchestrator.orders,
    )

    m = orchestrator.create_mandate({"title": "Poll Test", "quantity": 10, "max_unit_price": 1200.0, "max_total_budget": 12000.0})
    s = await orchestrator.run_autonomous_negotiation(m.id)
    assert s.status.value == "AGREEMENT_REACHED"
    order, bundle = await orchestrator.finalize_agreement_and_authorize_escrow(s.session_id)

    # Advance to shipment
    order, bundle = await orchestrator.advance_to_shipment_milestone(order.order_id)
    assert order.status == EscrowStatus.IN_TRANSIT

    # Simulate PayPal mock order being COMPLETED on PayPal side
    orchestrator.paypal_provider.mock_orders[order.paypal_order_id]["status"] = "COMPLETED"

    reconciled = await polling_service.reconcile_order(order.order_id)
    assert reconciled["reconciled"] is True
    assert order.status == EscrowStatus.COMPLETED
    assert order.milestones[2].status == MilestoneStepStatus.COMPLETED
    assert order.milestones[2].released_amount == order.total_amount


@pytest.mark.asyncio
async def test_polling_service_background_lifecycle(orchestrator):
    """
    Test starting and stopping the background polling service loop.
    """
    polling_service = PollingFallbackService(
        paypal_provider=orchestrator.paypal_provider,
        orders_store=orchestrator.orders,
    )
    assert polling_service.is_running is False

    await polling_service.start_background_polling(interval_seconds=1)
    assert polling_service.is_running is True
    assert polling_service._task is not None

    await asyncio.sleep(0.1)

    polling_service.stop_background_polling()
    assert polling_service.is_running is False


def test_mandate_snapshot_signature_tamper_detection(orchestrator):
    """
    Test that tampering with mandate snapshot invalidates the digital signature.
    """
    mandate = orchestrator.create_mandate({
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
    })

    snapshot = mandate.model_dump()
    assert ProcurementMandate.verify_snapshot_signature(snapshot) is True

    # Tamper with the snapshot max price
    snapshot["max_unit_price"] = 9999.0
    assert ProcurementMandate.verify_snapshot_signature(snapshot) is False


def test_evidence_bundle_agreement_hash_verification(orchestrator):
    """
    Test that EvidenceBundleManager verifies canonical agreement hash and catches alterations.
    """
    mandate = orchestrator.create_mandate({"quantity": 10, "max_unit_price": 500.0, "max_total_budget": 5000.0})
    
    agreed_fields = {
        "agreement_id": "AGR-CANONICAL-TEST",
        "mandate_id": mandate.id,
        "vendor_id": "VEND-01",
        "vendor_name": "Supplier",
        "item_name": mandate.item_name,
        "final_unit_price": 480.0,
        "final_quantity": 10,
        "final_total": 4800.0,
        "lead_time_days": 4,
        "warranty_months": 24,
    }
    agreement_hash = compute_canonical_agreement_hash(agreed_fields)
    agreement = FinalAgreement(**agreed_fields, agreement_hash=agreement_hash)

    from app.models.escrow import EscrowOrder
    order = EscrowOrder(
        order_id="ESC-CANONICAL-TEST",
        mandate_id=mandate.id,
        agreement_id=agreement.agreement_id,
        vendor_id=agreement.vendor_id,
        vendor_name=agreement.vendor_name,
        item_name=agreement.item_name,
        quantity=agreement.final_quantity,
        unit_price=agreement.final_unit_price,
        total_amount=agreement.final_total,
    )
    session = NegotiationSession(
        session_id="NEG-CANONICAL-TEST",
        mandate_id=mandate.id,
        vendor_id=agreement.vendor_id,
        vendor_name=agreement.vendor_name,
        catalog_item_id="CH3-ITEM",
        initial_ask_price=500.0,
        agreement=agreement,
    )

    bundle = EvidenceBundleManager.create_bundle(mandate, session, agreement, order)
    report = EvidenceBundleManager.verify_bundle(bundle)
    assert report["agreement_hash_valid"] is True
    assert report["mandate_signature_valid"] is True
    assert report["root_seal_matches"] is True
    assert report["tamper_evident_valid"] is True

    # Mutate agreement payload
    bundle.agreement_payload["final_unit_price"] = 8888.0
    tampered_report = EvidenceBundleManager.verify_bundle(bundle)
    assert tampered_report["agreement_hash_valid"] is False
    assert tampered_report["root_seal_matches"] is False
    assert tampered_report["tamper_evident_valid"] is False
