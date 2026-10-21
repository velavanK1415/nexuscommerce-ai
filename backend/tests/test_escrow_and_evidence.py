import pytest
from datetime import datetime, timezone, timedelta

from app.models.mandate import ProcurementMandate
from app.models.negotiation import FinalAgreement, NegotiationSession, NegotiationProposal, ProposalSender
from app.models.escrow import EscrowStatus, MilestoneStepStatus
from app.core.policy_engine import PolicyEngine
from app.core.evidence_bundle import EvidenceBundleManager
from app.providers.paypal_provider import PayPalProvider


@pytest.fixture
def sample_setup():
    provider = PayPalProvider(demo_mode=True)
    engine = PolicyEngine(paypal_provider=provider)
    now = datetime.now(timezone.utc)

    mandate = ProcurementMandate(
        id="MAN-ESCROW-01",
        buyer_id="BUYER-CORP",
        buyer_name="Apex Corp",
        buyer_email="buyer@apex.io",
        title="Edge Hardware",
        target_categories=["Networking Hardware"],
        item_name="NexusEdge 100G",
        quantity=50,
        max_unit_price=1200.0,
        max_total_budget=60000.0,
        delivery_deadline=(now + timedelta(days=20)).isoformat(),
        expiry_timestamp=(now + timedelta(days=10)).isoformat(),
    )
    mandate.sign()

    from app.core.evidence_bundle import compute_canonical_agreement_hash
    agreed_fields = {
        "agreement_id": "AGR-TEST-900",
        "mandate_id": mandate.id,
        "vendor_id": "VEND-01",
        "vendor_name": "NexIQ Enterprise",
        "item_name": mandate.item_name,
        "final_unit_price": 1100.0,
        "final_quantity": 50,
        "final_total": 55000.0,
        "lead_time_days": 5,
        "warranty_months": 36,
    }
    agreement_hash = compute_canonical_agreement_hash(agreed_fields)

    agreement = FinalAgreement(
        **agreed_fields,
        agreement_hash=agreement_hash,
    )

    session = NegotiationSession(
        session_id="NEG-SESSION-01",
        mandate_id=mandate.id,
        vendor_id="VEND-01",
        vendor_name="NexIQ Enterprise",
        catalog_item_id="CH3-100G",
        initial_ask_price=1250.0,
        agreement=agreement,
        proposals=[
            NegotiationProposal(
                proposal_id="PROP-1",
                round_number=1,
                sender=ProposalSender.PROCURE_BOT,
                mandate_id=mandate.id,
                vendor_id="VEND-01",
                vendor_name="NexIQ Enterprise",
                item_name=mandate.item_name,
                proposed_unit_price=1050.0,
                proposed_quantity=50,
                proposed_total=52500.0,
                lead_time_days=5,
                rationale="Opening offer",
            ),
            NegotiationProposal(
                proposal_id="PROP-2",
                round_number=2,
                sender=ProposalSender.VENDOR_BOT,
                mandate_id=mandate.id,
                vendor_id="VEND-01",
                vendor_name="NexIQ Enterprise",
                item_name=mandate.item_name,
                proposed_unit_price=1100.0,
                proposed_quantity=50,
                proposed_total=55000.0,
                lead_time_days=5,
                rationale="Best counter offer",
            ),
        ],
    )
    return engine, provider, mandate, agreement, session


@pytest.mark.asyncio
async def test_full_escrow_milestone_progression(sample_setup):
    engine, provider, mandate, agreement, session = sample_setup

    # Milestone 1: PayPal Authorization
    escrow_order = await engine.authorize_paypal_escrow(mandate, agreement, provider)
    assert escrow_order.status == EscrowStatus.FUNDS_AUTHORIZED
    assert escrow_order.paypal_authorization_id is not None
    assert escrow_order.milestones[0].status == MilestoneStepStatus.COMPLETED
    assert escrow_order.milestones[1].status == MilestoneStepStatus.IN_PROGRESS

    # Create Evidence Bundle
    bundle = EvidenceBundleManager.create_bundle(mandate, session, agreement, escrow_order)
    assert bundle.bundle_root_hash != ""
    assert bundle.tamper_evident_valid is True

    # Milestone 2: Carrier Shipment Proof Ingestion
    tracking = "FDX-77401-EXP"
    proof = {"status": "IN_TRANSIT", "carrier_event": "DISPATCH_TERMINAL_SCAN"}
    updated_order = await engine.verify_carrier_milestone(
        escrow_order=escrow_order,
        carrier_name="FedEx",
        tracking_number=tracking,
        shipment_proof=proof,
        provider=provider,
    )
    assert updated_order.status == EscrowStatus.IN_TRANSIT
    assert updated_order.milestones[1].status == MilestoneStepStatus.COMPLETED
    assert updated_order.milestones[1].released_amount == 16500.0  # 30% of $55,000
    assert updated_order.milestones[1].paypal_request_id is not None
    assert updated_order.paypal_partial_capture_id is not None
    assert updated_order.milestones[2].status == MilestoneStepStatus.IN_PROGRESS

    EvidenceBundleManager.attach_carrier_proof(
        bundle=bundle,
        carrier_name="FedEx",
        tracking_number=tracking,
        carrier_event=proof["carrier_event"],
    )
    EvidenceBundleManager.attach_paypal_partial_capture_receipt(
        bundle=bundle,
        capture_id=updated_order.paypal_partial_capture_id,
        amount_captured=updated_order.milestones[1].released_amount,
        currency="USD",
        paypal_request_id=updated_order.milestones[1].paypal_request_id,
        fee=round(16500.0 * 0.029 + 0.30, 2),
        is_final_capture=False,
    )
    assert bundle.carrier_proof is not None
    assert bundle.paypal_partial_capture_receipt is not None

    # Milestone 3: Delivery Verification & Escrow Capture Release
    final_order = await engine.release_milestone_capture(
        escrow_order=updated_order,
        provider=provider,
    )
    assert final_order.status == EscrowStatus.COMPLETED
    assert final_order.paypal_capture_id is not None
    assert final_order.paypal_request_id_final is not None
    assert final_order.milestones[2].status == MilestoneStepStatus.COMPLETED
    assert final_order.milestones[2].released_amount == 38500.0  # 70% of $55,000
    assert final_order.total_released == 55000.0  # 100% reconciled

    EvidenceBundleManager.attach_paypal_capture_receipt(
        bundle=bundle,
        capture_id=final_order.paypal_capture_id,
        amount_captured=final_order.milestones[2].released_amount,
        currency="USD",
        paypal_request_id=final_order.paypal_request_id_final,
        is_final_capture=True,
    )
    assert bundle.paypal_capture_receipt is not None

    # Cryptographic verification check
    report = EvidenceBundleManager.verify_bundle(bundle)
    assert report["tamper_evident_valid"] is True
    assert report["dispute_defense_grade"] == "A+"
    assert report["paypal_partial_capture_verified"] is True
    assert report["paypal_capture_verified"] is True
    assert bundle.mandate_diff is not None
    assert bundle.mandate_diff["quantity_reconciled"] is True
    assert bundle.mandate_diff["budget_reconciled"] is True
    assert bundle.mandate_diff["unit_price_under_cap"] is True


def test_tamper_detection_in_evidence_bundle(sample_setup):
    _, _, mandate, agreement, session = sample_setup
    from app.models.escrow import EscrowOrder

    order = EscrowOrder(
        order_id="ESC-TAMPER-TEST",
        mandate_id=mandate.id,
        agreement_id=agreement.agreement_id,
        vendor_id="VEND-01",
        vendor_name="NexIQ",
        item_name="NexusEdge 100G",
        quantity=50,
        unit_price=1100.0,
        total_amount=55000.0,
        paypal_authorization_id="AUTH-ORIGINAL-1",
    )
    bundle = EvidenceBundleManager.create_bundle(mandate, session, agreement, order)
    original_hash = bundle.bundle_root_hash

    # Verification passes initially
    assert bundle.verify_integrity() is True

    # Tamper with the agreement unit price directly
    bundle.agreement_payload["final_unit_price"] = 9999.0
    # Verification MUST detect tampering!
    assert bundle.verify_integrity() is False
