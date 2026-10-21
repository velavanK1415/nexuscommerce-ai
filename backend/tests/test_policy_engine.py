import pytest
from datetime import datetime, timezone, timedelta

from app.models.mandate import ProcurementMandate, QualityTier
from app.models.negotiation import NegotiationSession, NegotiationProposal, ProposalSender
from app.core.policy_engine import PolicyEngine, PolicyDecisionType
from app.providers.paypal_provider import PayPalProvider


@pytest.fixture
def test_mandate():
    now = datetime.now(timezone.utc)
    return ProcurementMandate(
        id="MAN-POLICY-01",
        buyer_id="BUYER-01",
        buyer_name="Apex Global",
        buyer_email="buyer@apex.io",
        title="Edge Hardware",
        target_categories=["Networking Hardware"],
        item_name="NexusEdge Pro 100G",
        quantity=50,
        max_unit_price=1200.0,
        max_total_budget=60000.0,
        delivery_deadline=(now + timedelta(days=20)).isoformat(),
        expiry_timestamp=(now + timedelta(days=10)).isoformat(),
    )


@pytest.fixture
def policy_engine():
    provider = PayPalProvider(demo_mode=True)
    return PolicyEngine(paypal_provider=provider)


def test_valid_llm_proposal_is_approved(policy_engine, test_mandate):
    raw_proposal = {
        "unit_price": 1150.0,
        "quantity": 50,
        "lead_time_days": 5,
        "warranty_months": 24,
        "rationale": "Competitive enterprise pricing.",
    }
    decision, proposal = policy_engine.validate_raw_llm_proposal(
        mandate=test_mandate,
        raw_proposal=raw_proposal,
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        round_number=1,
    )
    assert decision.is_approved is True
    assert decision.decision == PolicyDecisionType.APPROVED
    assert proposal is not None
    assert proposal.proposed_total == 57500.0


def test_price_ceiling_violation_triggers_hitl_hold(policy_engine, test_mandate):
    # Propose $1400 when mandate max is $1200
    raw_proposal = {
        "unit_price": 1400.0,
        "quantity": 50,
        "lead_time_days": 5,
        "warranty_months": 24,
        "rationale": "Surge pricing.",
    }
    decision, proposal = policy_engine.validate_raw_llm_proposal(
        mandate=test_mandate,
        raw_proposal=raw_proposal,
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        round_number=1,
    )
    assert decision.is_approved is False
    assert decision.decision == PolicyDecisionType.HITL_HOLD
    assert any("UNIT_PRICE_EXCEEDED" in r for r in decision.violated_rules)


def test_budget_ceiling_violation_triggers_hitl_hold(policy_engine, test_mandate):
    # Unit price $1100 is ok, but quantity 60 puts total to $66,000 > $60,000 max budget
    raw_proposal = {
        "unit_price": 1100.0,
        "quantity": 60,
        "lead_time_days": 5,
        "warranty_months": 24,
    }
    decision, proposal = policy_engine.validate_raw_llm_proposal(
        mandate=test_mandate,
        raw_proposal=raw_proposal,
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        round_number=1,
    )
    assert decision.decision == PolicyDecisionType.HITL_HOLD
    assert any("TOTAL_BUDGET_EXCEEDED" in r for r in decision.violated_rules)
    assert any("QUANTITY_MISMATCH" in r for r in decision.violated_rules)


def test_malformed_llm_output_triggers_hitl_hold(policy_engine, test_mandate):
    # Non-dictionary or missing fields
    decision, _ = policy_engine.validate_raw_llm_proposal(
        mandate=test_mandate,
        raw_proposal="hallucinated string from broken llm",
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        round_number=1,
    )
    assert decision.decision == PolicyDecisionType.HITL_HOLD
    assert "SCHEMA_INVALID" in decision.violated_rules

    # Missing required field
    decision2, _ = policy_engine.validate_raw_llm_proposal(
        mandate=test_mandate,
        raw_proposal={"unit_price": 1100.0},
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        round_number=1,
    )
    assert decision2.decision == PolicyDecisionType.HITL_HOLD
    assert any("MISSING_FIELD" in r for r in decision2.violated_rules)


def test_human_supervisor_override(policy_engine, test_mandate):
    session = NegotiationSession(
        session_id="NEG-HITL-TEST",
        mandate_id=test_mandate.id,
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        catalog_item_id="CH3-100G",
        initial_ask_price=1250.0,
    )
    flagged = NegotiationProposal(
        proposal_id="PROP-FLAGGED",
        round_number=2,
        sender=ProposalSender.VENDOR_BOT,
        mandate_id=test_mandate.id,
        vendor_id="VEND-1",
        vendor_name="NexIQ",
        item_name=test_mandate.item_name,
        proposed_unit_price=1210.0,  # $10 over ceiling
        proposed_quantity=50,
        proposed_total=60500.0,
        lead_time_days=5,
        rationale="Slight bump due to air shipping.",
    )
    session.hitl_flagged_proposal = flagged

    agreement = policy_engine.hitl_override_approve(
        session=session,
        mandate=test_mandate,
        supervisor_notes="Approved by VP Procurement for expedited shipment.",
    )
    assert agreement is not None
    assert agreement.final_unit_price == 1210.0
    assert agreement.final_total == 60500.0
    assert "HITL_SUPERVISOR_OVERRIDE" in agreement.buyer_signature
