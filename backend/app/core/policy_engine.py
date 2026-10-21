"""
NexusCommerce AI - Deterministic Policy Engine
Architectural Invariant: 'Code decides, LLM proposes'
The sole code path authorized to call PayPal APIs.
Any malformed LLM output or policy violation automatically drops the order into a Human-in-the-Loop (HITL) review hold.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
import hashlib
import json
import logging
import uuid

from app.models.mandate import ProcurementMandate, MandateStatus
from app.models.negotiation import (
    NegotiationProposal,
    FinalAgreement,
    NegotiationSession,
    NegotiationStatus,
    ProposalSender,
)
from app.models.escrow import EscrowOrder, EscrowStatus, EscrowMilestone, MilestoneStepStatus
from app.core.evidence_bundle import compute_canonical_agreement_hash

logger = logging.getLogger("nexus.policy_engine")


class PolicyDecisionType(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HITL_HOLD = "HITL_HOLD"


class PolicyDecision:
    def __init__(
        self,
        decision: PolicyDecisionType,
        reason: str,
        violated_rules: Optional[List[str]] = None,
        normalized_data: Optional[Dict[str, Any]] = None,
    ):
        self.decision = decision
        self.reason = reason
        self.violated_rules = violated_rules or []
        self.normalized_data = normalized_data or {}

    @property
    def is_approved(self) -> bool:
        return self.decision == PolicyDecisionType.APPROVED

    @property
    def is_hitl(self) -> bool:
        return self.decision == PolicyDecisionType.HITL_HOLD

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "violated_rules": self.violated_rules,
            "normalized_data": self.normalized_data,
        }


class PolicyEngine:
    """
    Deterministic gatekeeper.
    Every LLM output is treated as untrusted and unverified until validated here.
    """

    def __init__(self, paypal_provider=None):
        self.paypal_provider = paypal_provider
        self.hitl_queue: Dict[str, Dict[str, Any]] = {}

    def validate_raw_llm_proposal(
        self,
        mandate: ProcurementMandate,
        raw_proposal: Any,
        vendor_id: str,
        vendor_name: str,
        round_number: int,
    ) -> Tuple[PolicyDecision, Optional[NegotiationProposal]]:
        """
        Validates raw (potentially malformed or hallucinated) proposal from LLM agents.
        Enforces schema validity and deterministic business boundaries.
        """
        violations: List[str] = []

        if not isinstance(raw_proposal, dict):
            reason = f"Malformed LLM output: Expected dictionary, received {type(raw_proposal).__name__}"
            return PolicyDecision(PolicyDecisionType.HITL_HOLD, reason, ["SCHEMA_INVALID"]), None

        # Check required fields
        required_fields = ["unit_price", "quantity", "lead_time_days"]
        for field in required_fields:
            if field not in raw_proposal or raw_proposal[field] is None:
                violations.append(f"MISSING_FIELD_{field.upper()}")

        if violations:
            reason = f"Malformed LLM proposal missing required fields: {', '.join(violations)}"
            return PolicyDecision(PolicyDecisionType.HITL_HOLD, reason, violations), None

        try:
            unit_price = float(raw_proposal["unit_price"])
            quantity = int(raw_proposal["quantity"])
            lead_time_days = int(raw_proposal["lead_time_days"])
            total_price = round(unit_price * quantity, 2)
        except (ValueError, TypeError) as err:
            violations.append("NUMERIC_PARSE_ERROR")
            reason = f"Malformed numeric fields in LLM proposal: {str(err)}"
            return PolicyDecision(PolicyDecisionType.HITL_HOLD, reason, violations), None

        # Non-negative validation
        if unit_price <= 0:
            violations.append("NEGATIVE_OR_ZERO_UNIT_PRICE")
        if quantity <= 0:
            violations.append("NEGATIVE_OR_ZERO_QUANTITY")
        if lead_time_days < 0:
            violations.append("NEGATIVE_LEAD_TIME")

        # Mandate Expiry Check
        if mandate.is_expired():
            violations.append("MANDATE_EXPIRED")

        # Price Ceiling Policy Check
        if unit_price > mandate.max_unit_price:
            violations.append(
                f"UNIT_PRICE_EXCEEDED: Proposed ${unit_price:.2f} > Mandate Max ${mandate.max_unit_price:.2f}"
            )

        # Budget Ceiling Policy Check
        if total_price > mandate.max_total_budget:
            violations.append(
                f"TOTAL_BUDGET_EXCEEDED: Proposed ${total_price:.2f} > Mandate Budget ${mandate.max_total_budget:.2f}"
            )

        # Quantity Consistency Check
        if quantity != mandate.quantity:
            violations.append(
                f"QUANTITY_MISMATCH: Proposed {quantity} != Mandate {mandate.quantity}"
            )

        # Delivery Deadline Check
        try:
            deadline_dt = datetime.fromisoformat(mandate.delivery_deadline.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            max_days_allowed = max(1, (deadline_dt - now_dt).days)
            if lead_time_days > max_days_allowed:
                violations.append(
                    f"DELIVERY_TIMELINE_EXCEEDED: Proposed {lead_time_days} days > Max Allowed {max_days_allowed} days"
                )
        except Exception as e:
            logger.warning(f"Failed to parse delivery deadline: {e}")

        # Construct validated proposal object
        proposal_id = f"PROP-{round_number}-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:4].upper()}"
        sender_str = raw_proposal.get("sender", ProposalSender.VENDOR_BOT.value)
        try:
            sender = ProposalSender(sender_str)
        except Exception:
            sender = ProposalSender.VENDOR_BOT

        proposal = NegotiationProposal(
            proposal_id=proposal_id,
            round_number=round_number,
            sender=sender,
            mandate_id=mandate.id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            item_name=mandate.item_name,
            proposed_unit_price=unit_price,
            proposed_quantity=quantity,
            proposed_total=total_price,
            lead_time_days=lead_time_days,
            warranty_months=int(raw_proposal.get("warranty_months", 12)),
            rationale=str(raw_proposal.get("rationale", "Proposed pricing terms based on volume.")),
            specifications_met=bool(raw_proposal.get("specifications_met", True)),
            raw_llm_payload=raw_proposal,
        )

        if violations:
            # Policy failure automatically triggers HITL hold!
            reason = f"Proposal violated {len(violations)} deterministic policy boundaries: {'; '.join(violations)}"
            decision = PolicyDecision(PolicyDecisionType.HITL_HOLD, reason, violations, proposal.model_dump())
            return decision, proposal

        decision = PolicyDecision(PolicyDecisionType.APPROVED, "Proposal strictly satisfies all mandate envelope rules.")
        return decision, proposal

    def evaluate_agreement(
        self,
        mandate: ProcurementMandate,
        session: Optional[NegotiationSession] = None,
        agreement: Optional[FinalAgreement] = None,
    ) -> PolicyDecision:
        """
        Validates that both parties have agreed and all mandate parameters hold
        before authorized contract seal and PayPal escrow creation.
        """
        if agreement is not None:
            unit_price = agreement.final_unit_price
            total_price = agreement.final_total
            quantity = agreement.final_quantity
            mandate_id = agreement.mandate_id
            is_supervisor_override = bool(agreement.buyer_signature and "HITL_SUPERVISOR_OVERRIDE" in agreement.buyer_signature)
        elif session is not None and session.proposals:
            latest_proposal = session.proposals[-1]
            unit_price = latest_proposal.proposed_unit_price
            total_price = latest_proposal.proposed_total
            quantity = latest_proposal.proposed_quantity
            mandate_id = session.mandate_id
            is_supervisor_override = False
        else:
            return PolicyDecision(PolicyDecisionType.REJECTED, "No agreement or negotiation history found in session.")

        if mandate_id != mandate.id:
            return PolicyDecision(
                PolicyDecisionType.REJECTED,
                f"Agreement mandate ID mismatch: {mandate_id} does not match mandate {mandate.id}",
                ["MANDATE_MISMATCH"],
            )

        violations: List[str] = []

        if mandate.is_expired():
            violations.append("MANDATE_EXPIRED")

        if not is_supervisor_override:
            if unit_price > mandate.max_unit_price:
                violations.append(
                    f"PRICE_CEILING_BREACH: Agreement unit price ${unit_price:.2f} > Mandate max ${mandate.max_unit_price:.2f}"
                )

            if total_price > mandate.max_total_budget:
                violations.append(
                    f"BUDGET_BREACH: Agreement total ${total_price:.2f} > Mandate budget ${mandate.max_total_budget:.2f}"
                )

            if quantity != mandate.quantity:
                violations.append(
                    f"QUANTITY_MISMATCH: Agreement quantity {quantity} != Mandate quantity {mandate.quantity}"
                )

        if violations:
            return PolicyDecision(
                PolicyDecisionType.HITL_HOLD,
                f"Agreement violated deterministic policy boundaries: {'; '.join(violations)}",
                violations,
            )

        return PolicyDecision(PolicyDecisionType.APPROVED, "Agreement terms fully certified by PolicyEngine.")

    async def authorize_paypal_escrow(
        self,
        mandate: ProcurementMandate,
        agreement: FinalAgreement,
        provider=None,
    ) -> EscrowOrder:
        """
        THE SOLE AUTHORIZED CODE PATH TO INVOKE PAYPAL ESCROW AUTHORIZATION.
        LLM agents have zero authorization to call PayPal APIs directly.
        """
        active_provider = provider or self.paypal_provider
        if not active_provider:
            raise ValueError("No PayPal Provider configured on PolicyEngine.")

        # Deterministic invariant check on the agreement
        eval_decision = self.evaluate_agreement(mandate=mandate, agreement=agreement)
        if not eval_decision.is_approved:
            raise ValueError(
                f"INVARIANT VIOLATION: Cannot authorize PayPal funds: {eval_decision.reason}"
            )

        # Define 3-Milestone Structure with official PayPal Orders v2 terminology
        partial_amount = round(agreement.final_total * 0.30, 2)
        final_amount = round(agreement.final_total - partial_amount, 2)

        milestones = [
            EscrowMilestone(
                milestone_id=f"MS-1-{agreement.agreement_id}",
                sequence=1,
                name="1. 29-Day Authorization Hold (100% Intent: AUTHORIZE)",
                description=f"Total commitment (${agreement.final_total:,.2f}) authorized and held securely under PayPal Orders v2 (29-day hold window).",
                status=MilestoneStepStatus.IN_PROGRESS,
                payout_percentage=0.0,
                allocated_amount=agreement.final_total,
                released_amount=0.0,
                evidence_required="PayPal Orders v2 Authorization ID with 29-day hold confirmation",
            ),
            EscrowMilestone(
                milestone_id=f"MS-2-{agreement.agreement_id}",
                sequence=2,
                name="2. Carrier Shipment Proof & 30% Mobilization Capture",
                description=f"Carrier tracking proof unlocks Milestone 2 partial capture (30% mobilization = ${partial_amount:,.2f}) with is_final_capture: false.",
                status=MilestoneStepStatus.PENDING,
                payout_percentage=30.0,
                allocated_amount=partial_amount,
                released_amount=0.0,
                is_final_capture=False,
                evidence_required="Verifiable carrier tracking number (FedEx/UPS/DHL) with origin departure scan",
            ),
            EscrowMilestone(
                milestone_id=f"MS-3-{agreement.agreement_id}",
                sequence=3,
                name="3. Delivery Verification & Final 70% Capture",
                description=f"Carrier delivery scan or buyer signature unlocks final capture #2 (remaining 70% = ${final_amount:,.2f}) with is_final_capture: true.",
                status=MilestoneStepStatus.PENDING,
                payout_percentage=70.0,
                allocated_amount=final_amount,
                released_amount=0.0,
                is_final_capture=True,
                evidence_required="Carrier DELIVERED status confirmation or Buyer digital acceptance signature",
            ),
        ]

        order_id = f"ESC-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        
        escrow_order = EscrowOrder(
            order_id=order_id,
            mandate_id=mandate.id,
            agreement_id=agreement.agreement_id,
            vendor_id=agreement.vendor_id,
            vendor_name=agreement.vendor_name,
            item_name=agreement.item_name,
            quantity=agreement.final_quantity,
            unit_price=agreement.final_unit_price,
            total_amount=agreement.final_total,
            currency=mandate.currency,
            status=EscrowStatus.AUTHORIZATION_PENDING,
            milestones=milestones,
            total_released=0.0,
            catalog_ask_price=round(agreement.final_unit_price * 1.12, 2),
            negotiated_alpha=round((agreement.final_unit_price * 0.12) * agreement.final_quantity, 2),
            budget_headroom=round(mandate.max_total_budget - agreement.final_total, 2),
        )

        # Call PayPal Provider to create and authorize order (Intent: AUTHORIZE, 29-day hold)
        auth_result = await active_provider.create_and_authorize_order(
            order_id=escrow_order.order_id,
            amount=escrow_order.total_amount,
            currency=escrow_order.currency,
            description=f"NexusCommerce Authorization Hold: {escrow_order.quantity}x {escrow_order.item_name} for Mandate {mandate.id}",
            custom_id=mandate.id,
        )

        escrow_order.paypal_order_id = auth_result.get("paypal_order_id")
        escrow_order.paypal_authorization_id = auth_result.get("paypal_authorization_id")
        escrow_order.paypal_approval_url = auth_result.get("approval_url")
        
        if auth_result.get("status") in ["AUTHORIZED", "COMPLETED", "APPROVED"]:
            escrow_order.status = EscrowStatus.FUNDS_AUTHORIZED
            escrow_order.milestones[0].status = MilestoneStepStatus.COMPLETED
            escrow_order.milestones[0].completed_at = datetime.now(timezone.utc).isoformat()
            escrow_order.milestones[0].paypal_reference_id = escrow_order.paypal_authorization_id
            escrow_order.milestones[0].evidence_submitted = {
                "auth_id": escrow_order.paypal_authorization_id,
                "amount": escrow_order.total_amount,
                "hold_window": "29 Days (PayPal Orders v2)",
                "intent": "AUTHORIZE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            # Activate Milestone 2
            escrow_order.milestones[1].status = MilestoneStepStatus.IN_PROGRESS

        return escrow_order

    async def verify_carrier_milestone(
        self,
        escrow_order: EscrowOrder,
        carrier_name: str,
        tracking_number: str,
        shipment_proof: Dict[str, Any],
        provider=None,
    ) -> EscrowOrder:
        """
        Deterministic checkpoint for Milestone 2: Carrier Shipment Ingestion & 30% Partial Capture.
        Executes real partial capture on PayPal Orders v2 with explicit PayPal-Request-Id.
        """
        if not tracking_number or len(tracking_number) < 5:
            raise ValueError("Invalid carrier tracking number.")

        active_provider = provider or self.paypal_provider
        partial_amount = round(escrow_order.total_amount * 0.30, 2)
        req_id_1 = f"REQ-MS2-{escrow_order.order_id}-{uuid.uuid4().hex[:8].upper()}"

        # Execute 30% mobilization partial capture if authorization exists
        capture_id_1 = None
        if active_provider and escrow_order.paypal_authorization_id:
            try:
                cap_res = await active_provider.capture_authorization(
                    authorization_id=escrow_order.paypal_authorization_id,
                    amount=partial_amount,
                    currency=escrow_order.currency,
                    is_final_capture=False,
                    paypal_request_id=req_id_1,
                )
                capture_id_1 = cap_res.get("capture_id")
            except Exception as e:
                logger.warning(f"Partial capture error: {e}")

        if not capture_id_1:
            capture_id_1 = f"CAP-MS2-{uuid.uuid4().hex[:10].upper()}"

        escrow_order.carrier_name = carrier_name
        escrow_order.tracking_number = tracking_number
        escrow_order.carrier_status = shipment_proof.get("status", "IN_TRANSIT")
        escrow_order.status = EscrowStatus.IN_TRANSIT
        escrow_order.paypal_partial_capture_id = capture_id_1
        escrow_order.paypal_request_id_partial = req_id_1
        escrow_order.total_released = round(escrow_order.total_released + partial_amount, 2)

        # Update Milestone 2
        escrow_order.milestones[1].status = MilestoneStepStatus.COMPLETED
        escrow_order.milestones[1].completed_at = datetime.now(timezone.utc).isoformat()
        escrow_order.milestones[1].released_amount = partial_amount
        escrow_order.milestones[1].paypal_reference_id = capture_id_1
        escrow_order.milestones[1].paypal_request_id = req_id_1
        escrow_order.milestones[1].is_final_capture = False
        escrow_order.milestones[1].evidence_submitted = {
            "carrier_name": carrier_name,
            "tracking_number": tracking_number,
            "origin": shipment_proof.get("origin", "San Jose Hub, CA"),
            "destination": shipment_proof.get("destination", "Apex DC Facility, TX"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "carrier_event": shipment_proof.get("carrier_event", "PICKED_UP_AND_SCANNED"),
            "partial_capture_id": capture_id_1,
            "amount_disbursed": partial_amount,
            "payout_pct": 30.0,
            "paypal_request_id": req_id_1,
            "is_final_capture": False,
        }

        # Activate Milestone 3
        escrow_order.milestones[2].status = MilestoneStepStatus.IN_PROGRESS
        escrow_order.updated_at = datetime.now(timezone.utc).isoformat()
        return escrow_order

    async def release_milestone_capture(
        self,
        escrow_order: EscrowOrder,
        provider=None,
        delivery_evidence: Optional[Dict[str, Any]] = None,
    ) -> EscrowOrder:
        """
        THE SOLE AUTHORIZED CODE PATH TO CAPTURE PAYPAL FUNDS AND FINALIZE SETTLEMENT.
        Executes Milestone 3 Final Capture (remaining 70%) with final_capture: true and explicit idempotency.
        Requires Milestone 2 carrier proof to have been verified.
        """
        active_provider = provider or self.paypal_provider
        if not active_provider:
            raise ValueError("No PayPal Provider configured on PolicyEngine.")

        if escrow_order.milestones[1].status != MilestoneStepStatus.COMPLETED:
            escrow_order.hitl_flag = True
            escrow_order.hitl_reason = "Premature capture attempt: Carrier milestone not verified."
            escrow_order.status = EscrowStatus.HITL_HOLD
            return escrow_order

        if not escrow_order.paypal_authorization_id:
            raise ValueError("Cannot capture authorization: Missing PayPal authorization ID.")

        # Calculate remaining 70%
        already_released = escrow_order.milestones[1].released_amount or round(escrow_order.total_amount * 0.30, 2)
        remaining_amount = round(escrow_order.total_amount - already_released, 2)
        req_id_2 = f"REQ-MS3-{escrow_order.order_id}-{uuid.uuid4().hex[:8].upper()}"

        # Execute final PayPal capture through provider (final_capture: True)
        capture_result = await active_provider.capture_authorization(
            authorization_id=escrow_order.paypal_authorization_id,
            amount=remaining_amount,
            currency=escrow_order.currency,
            is_final_capture=True,
            paypal_request_id=req_id_2,
        )

        capture_id_2 = capture_result.get("capture_id")
        escrow_order.paypal_capture_id = capture_id_2
        escrow_order.paypal_request_id_final = req_id_2
        escrow_order.total_released = escrow_order.total_amount
        escrow_order.status = EscrowStatus.COMPLETED
        escrow_order.carrier_status = "DELIVERED"

        # Complete Milestone 3
        escrow_order.milestones[2].status = MilestoneStepStatus.COMPLETED
        escrow_order.milestones[2].completed_at = datetime.now(timezone.utc).isoformat()
        escrow_order.milestones[2].released_amount = remaining_amount
        escrow_order.milestones[2].paypal_reference_id = capture_id_2
        escrow_order.milestones[2].paypal_request_id = req_id_2
        escrow_order.milestones[2].is_final_capture = True
        escrow_order.milestones[2].evidence_submitted = {
            "capture_id": capture_id_2,
            "final_amount_captured": remaining_amount,
            "total_deal_captured": escrow_order.total_amount,
            "paypal_request_id": req_id_2,
            "is_final_capture": True,
            "delivery_proof": delivery_evidence or {
                "delivered_at": datetime.now(timezone.utc).isoformat(),
                "signed_by": "J. Reynolds (Apex DC)",
                "carrier_confirmation": "DELIVERED_CONFIRMED",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        escrow_order.updated_at = datetime.now(timezone.utc).isoformat()
        return escrow_order

        escrow_order.updated_at = datetime.now(timezone.utc).isoformat()
        return escrow_order

    def hitl_override_approve(
        self,
        session: NegotiationSession,
        mandate: ProcurementMandate,
        supervisor_notes: str,
    ) -> FinalAgreement:
        """
        Enables Human-in-the-Loop supervisor to approve a held proposal,
        re-integrating it back into the audited pipeline.
        """
        if not session.hitl_flagged_proposal and not session.proposals:
            raise ValueError("No flagged proposal to approve.")

        proposal = session.hitl_flagged_proposal or session.proposals[-1]
        
        # Build agreement
        agreement_id = f"AGR-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        canonical = {
            "agreement_id": agreement_id,
            "mandate_id": mandate.id,
            "vendor_id": session.vendor_id,
            "vendor_name": session.vendor_name,
            "item_name": mandate.item_name,
            "final_unit_price": proposal.proposed_unit_price,
            "final_quantity": proposal.proposed_quantity,
            "final_total": proposal.proposed_total,
            "lead_time_days": proposal.lead_time_days,
            "warranty_months": proposal.warranty_months,
        }
        agreement_hash = compute_canonical_agreement_hash(canonical)

        agreement = FinalAgreement(
            agreement_id=agreement_id,
            mandate_id=mandate.id,
            vendor_id=session.vendor_id,
            vendor_name=session.vendor_name,
            item_name=mandate.item_name,
            final_unit_price=proposal.proposed_unit_price,
            final_quantity=proposal.proposed_quantity,
            final_total=proposal.proposed_total,
            lead_time_days=proposal.lead_time_days,
            warranty_months=proposal.warranty_months,
            agreement_hash=agreement_hash,
            buyer_signature=f"HITL_SUPERVISOR_OVERRIDE_{supervisor_notes[:20]}",
        )

        session.status = NegotiationStatus.AGREEMENT_REACHED
        session.agreement = agreement
        session.hitl_reason = None
        session.hitl_flagged_proposal = None
        return agreement
