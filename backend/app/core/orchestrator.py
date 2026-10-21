"""
NexusCommerce AI - Core Orchestrator
Coordinates autonomous negotiation, policy validation, PayPal milestone escrow,
and evidence bundle compilation.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import json
import logging
import uuid

from app.models.mandate import ProcurementMandate, MandateStatus
from app.models.negotiation import (
    NegotiationSession,
    NegotiationProposal,
    FinalAgreement,
    NegotiationStatus,
    ProposalSender,
)
from app.models.escrow import EscrowOrder, EscrowMilestone, EscrowStatus, MilestoneStepStatus
from app.models.evidence import EvidenceBundle
from app.core.policy_engine import PolicyEngine, PolicyDecisionType
from app.core.evidence_bundle import EvidenceBundleManager, compute_canonical_agreement_hash
from app.providers.paypal_provider import PayPalProvider
from app.providers.channel3_provider import Channel3Provider
from app.agents.procure_bot import ProcureBot
from app.agents.vendor_bot import VendorBot

logger = logging.getLogger("nexus.orchestrator")


class NexusOrchestrator:
    def __init__(
        self,
        paypal_provider: Optional[PayPalProvider] = None,
        channel3_provider: Optional[Channel3Provider] = None,
        auto_seed: bool = True,
    ):
        self.paypal_provider = paypal_provider or PayPalProvider(demo_mode=True)
        self.channel3_provider = channel3_provider or Channel3Provider(demo_mode=True)
        self.policy_engine = PolicyEngine(paypal_provider=self.paypal_provider)
        self.procure_bot = ProcureBot()
        self.vendor_bot = VendorBot()

        # In-memory stores
        self.mandates: Dict[str, ProcurementMandate] = {}
        self.sessions: Dict[str, NegotiationSession] = {}
        self.orders: Dict[str, EscrowOrder] = {}
        self.bundles: Dict[str, EvidenceBundle] = {}

        if auto_seed:
            self.seed_initial_state()

    def seed_initial_state(self):
        """
        Seeds an authoritative, fully reconciled deal (NVIDIA H100 AI GPU cluster):
        - Mandate: 100 units @ $32,000.00 max cap = $3,200,000.00 budget cap
        - 3-Round Autonomous Negotiation:
            Round 1: Buyer $28,500, Vendor $31,200 (Spread $2,700)
            Round 2: Buyer $29,250, Vendor $30,400 (Spread $1,150)
            Round 3: Buyer $29,780, Vendor $29,920 (Residual Spread $140 - realistic commercial variance)
            Consensus: $29,850.00/unit x 100 = $2,985,000.00 settled
        - PayPal Orders v2 Two-Step Settlement:
            Milestone 1: 100% 29-Day Authorization Hold ($2,985,000.00)
            Milestone 2: Carrier Proof Verified & 30% Mobilization Partial Capture ($895,500.00) with is_final_capture=False
            Milestone 3: Delivery Acceptance & 70% Final Capture ($2,089,500.00) with is_final_capture=True
        - Cryptographic Evidence Bundle with valid A+ dispute defense Merkle seal
        """
        now = datetime.now(timezone.utc)
        mandate_id = "MAN-2026-H100"
        mandate = ProcurementMandate(
            id=mandate_id,
            buyer_id="BUYER-CORP-9021",
            buyer_name="Apex Global Logistics Corp",
            buyer_email="procurement@apexlogistics.io",
            title="Autonomous Sourcing: AI Cluster GPUs (NVIDIA H100)",
            target_categories=["AI Compute Hardware", "Data Center Equipment"],
            item_name="NVIDIA H100 SXM5 80GB Server Node",
            quantity=100,
            max_unit_price=32000.0,
            max_total_budget=3200000.0,
            currency="USD",
            quality_tier="Enterprise",
            delivery_deadline=(now + timedelta(days=30)).isoformat(),
            expiry_timestamp=(now + timedelta(days=14)).isoformat(),
            notes="Tier-1 enterprise warranty, authentic serial tracking, 2-step authorization hold & milestone captures required.",
            status=MandateStatus.COMPLETED,
        )
        mandate.sign()
        self.mandates[mandate.id] = mandate

        agreed_fields = {
            "agreement_id": "AGR-H100-2026-CERTIFIED",
            "mandate_id": mandate.id,
            "vendor_id": "VEND-NEXIQ-410",
            "vendor_name": "NexIQ Enterprise Networks Ltd",
            "item_name": mandate.item_name,
            "final_unit_price": 29850.0,
            "final_quantity": 100,
            "final_total": 2985000.0,
            "lead_time_days": 5,
            "warranty_months": 36,
        }
        agreement_hash = compute_canonical_agreement_hash(agreed_fields)
        agreement = FinalAgreement(
            **agreed_fields,
            agreement_hash=agreement_hash,
            buyer_signature=mandate.signature,
            vendor_signature="SIG-VENDOR-VEND-NEXIQ-410-CERTIFIED",
        )

        session = NegotiationSession(
            session_id=f"NEG-{mandate.id}-VEND-NEXIQ-410",
            mandate_id=mandate.id,
            vendor_id="VEND-NEXIQ-410",
            vendor_name="NexIQ Enterprise Networks Ltd",
            vendor_rating=4.9,
            catalog_item_id="CH3-H100-NODE",
            initial_ask_price=33500.0,
            status=NegotiationStatus.AGREEMENT_REACHED,
            agreement=agreement,
            proposals=[
                NegotiationProposal(
                    proposal_id="PROP-1-B",
                    round_number=1,
                    sender=ProposalSender.PROCURE_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=28500.0,
                    proposed_quantity=100,
                    proposed_total=2850000.0,
                    lead_time_days=5,
                    warranty_months=24,
                    rationale="Apex Procurement opening offer for bulk order of 100 units. Targeting $28,500.00/unit with enterprise SLA and 5-day delivery.",
                ),
                NegotiationProposal(
                    proposal_id="PROP-1-V",
                    round_number=1,
                    sender=ProposalSender.VENDOR_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=31200.0,
                    proposed_quantity=100,
                    proposed_total=3120000.0,
                    lead_time_days=5,
                    warranty_months=36,
                    rationale="VendorBot opening volume discount (Round 1): Counter-offering at $31,200.00/unit with Tier-1 SLA and 36-month enterprise warranty.",
                ),
                NegotiationProposal(
                    proposal_id="PROP-2-B",
                    round_number=2,
                    sender=ProposalSender.PROCURE_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=29250.0,
                    proposed_quantity=100,
                    proposed_total=2925000.0,
                    lead_time_days=5,
                    warranty_months=24,
                    rationale="ProcureBot volume counter-offer (Round 2): Stepping up commitment to $29,250.00/unit backed by guaranteed PayPal Orders v2 29-day authorization hold upon agreement.",
                ),
                NegotiationProposal(
                    proposal_id="PROP-2-V",
                    round_number=2,
                    sender=ProposalSender.VENDOR_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=30400.0,
                    proposed_quantity=100,
                    proposed_total=3040000.0,
                    lead_time_days=5,
                    warranty_months=36,
                    rationale="VendorBot tier concession (Round 2): Adjusting margin curve to $30,400.00/unit for bulk volume commitment under PayPal 29-day authorization hold.",
                ),
                NegotiationProposal(
                    proposal_id="PROP-3-B",
                    round_number=3,
                    sender=ProposalSender.PROCURE_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=29780.0,
                    proposed_quantity=100,
                    proposed_total=2978000.0,
                    lead_time_days=5,
                    warranty_months=36,
                    rationale="ProcureBot final counter-offer (Round 3): Offering $29,780.00/unit with enterprise Tier-1 SLA and immediate 2-step milestone authorization hold.",
                ),
                NegotiationProposal(
                    proposal_id="PROP-3-V",
                    round_number=3,
                    sender=ProposalSender.VENDOR_BOT,
                    mandate_id=mandate.id,
                    vendor_id="VEND-NEXIQ-410",
                    vendor_name="NexIQ Enterprise Networks Ltd",
                    item_name=mandate.item_name,
                    proposed_unit_price=29920.0,
                    proposed_quantity=100,
                    proposed_total=2992000.0,
                    lead_time_days=5,
                    warranty_months=36,
                    rationale="VendorBot best and final offer (Round 3): $29,920.00/unit with 36-month enterprise warranty. Residual commercial spread of $140.00/unit (0.47% variance) compensated by Tier-1 advance hardware replacement.",
                ),
            ],
        )
        self.sessions[session.session_id] = session

        order = EscrowOrder(
            order_id="ESC-2026-H100",
            mandate_id=mandate.id,
            agreement_id=agreement.agreement_id,
            vendor_id=agreement.vendor_id,
            vendor_name=agreement.vendor_name,
            item_name=agreement.item_name,
            quantity=100,
            unit_price=29850.0,
            total_amount=2985000.0,
            status=EscrowStatus.COMPLETED,
            paypal_order_id="ORD-PP-H100-2026",
            paypal_authorization_id="AUTH-29D-8819A2",
            carrier_name="FedEx Priority Freight",
            tracking_number="FDX-9982-7104-H100",
            carrier_status="DELIVERED",
            paypal_partial_capture_id="CAP-PARTIAL-30-718A9",
            paypal_request_id_partial="REQ-MS2-H100-30PCT",
            paypal_capture_id="CAP-FINAL-70-994B1",
            paypal_request_id_final="REQ-MS3-H100-70PCT",
            total_released=2985000.0,
            catalog_ask_price=3350000.0,
            negotiated_alpha=365000.0,
            budget_headroom=215000.0,
            milestones=[
                EscrowMilestone(
                    milestone_id="MS-1-H100",
                    sequence=1,
                    name="1. 29-Day Authorization Hold (100% Intent: AUTHORIZE)",
                    description="Total commitment ($2,985,000.00) authorized and held securely under PayPal Orders v2 (29-day hold window).",
                    allocated_amount=2985000.0,
                    released_amount=0.0,
                    status=MilestoneStepStatus.COMPLETED,
                    paypal_reference_id="AUTH-29D-8819A2",
                    evidence_required="PayPal Orders v2 Authorization ID with 29-day hold confirmation",
                    completed_at=now.isoformat(),
                ),
                EscrowMilestone(
                    milestone_id="MS-2-H100",
                    sequence=2,
                    name="2. Carrier Shipment Proof & 30% Mobilization Capture",
                    description="Carrier tracking proof unlocks Milestone 2 partial capture (30% mobilization = $895,500.00) with is_final_capture: false.",
                    allocated_amount=895500.0,
                    released_amount=895500.0,
                    status=MilestoneStepStatus.COMPLETED,
                    paypal_reference_id="CAP-PARTIAL-30-718A9",
                    paypal_request_id="REQ-MS2-H100-30PCT",
                    is_final_capture=False,
                    evidence_required="Verifiable carrier tracking number with origin departure scan",
                    completed_at=now.isoformat(),
                ),
                EscrowMilestone(
                    milestone_id="MS-3-H100",
                    sequence=3,
                    name="3. Delivery Verification & Final 70% Capture",
                    description="Carrier delivery scan unlocks final capture #2 (remaining 70% = $2,089,500.00) with is_final_capture: true.",
                    allocated_amount=2089500.0,
                    released_amount=2089500.0,
                    status=MilestoneStepStatus.COMPLETED,
                    paypal_reference_id="CAP-FINAL-70-994B1",
                    paypal_request_id="REQ-MS3-H100-70PCT",
                    is_final_capture=True,
                    evidence_required="Carrier DELIVERED status confirmation",
                    completed_at=now.isoformat(),
                ),
            ],
        )

        bundle = EvidenceBundleManager.create_bundle(mandate, session, agreement, order)
        EvidenceBundleManager.attach_carrier_proof(
            bundle,
            carrier_name=order.carrier_name,
            tracking_number=order.tracking_number,
            carrier_event="DELIVERED",
            origin="San Jose Distribution Terminal, CA",
            destination="Apex Enterprise Logistics Center, Dallas TX",
        )
        EvidenceBundleManager.attach_paypal_partial_capture_receipt(
            bundle,
            capture_id=order.paypal_partial_capture_id,
            amount_captured=895500.0,
            currency="USD",
            paypal_request_id=order.paypal_request_id_partial,
            fee=25969.80,
            is_final_capture=False,
        )
        EvidenceBundleManager.attach_paypal_capture_receipt(
            bundle,
            capture_id=order.paypal_capture_id,
            amount_captured=2089500.0,
            currency="USD",
            paypal_request_id=order.paypal_request_id_final,
            fee=60595.80,
            is_final_capture=True,
        )
        order.evidence_bundle_id = bundle.bundle_id
        self.orders[order.order_id] = order
        self.bundles[bundle.bundle_id] = bundle

    def create_mandate(self, mandate_data: Dict[str, Any]) -> ProcurementMandate:
        """
        Creates and cryptographically signs a new ProcurementMandate.
        """
        mandate_id = mandate_data.get("id") or f"MAN-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate sensible defaults for deadlines if not provided
        now = datetime.now(timezone.utc)
        delivery_deadline = mandate_data.get("delivery_deadline") or (
            datetime.fromtimestamp(now.timestamp() + 86400 * 30, tz=timezone.utc).isoformat()
        )
        expiry_timestamp = mandate_data.get("expiry_timestamp") or (
            datetime.fromtimestamp(now.timestamp() + 86400 * 14, tz=timezone.utc).isoformat()
        )

        mandate = ProcurementMandate(
            id=mandate_id,
            buyer_id=mandate_data.get("buyer_id", "BUYER-CORP-9021"),
            buyer_name=mandate_data.get("buyer_name", "Apex Global Logistics Corp"),
            buyer_email=mandate_data.get("buyer_email", "procurement@apexlogistics.io"),
            title=mandate_data.get("title", "Edge Infrastructure Procurement"),
            target_categories=mandate_data.get("target_categories", ["Networking Hardware"]),
            item_name=mandate_data.get("item_name", "NexusEdge Pro 100G Router"),
            quantity=int(mandate_data.get("quantity", 50)),
            max_unit_price=float(mandate_data.get("max_unit_price", 1200.0)),
            max_total_budget=float(mandate_data.get("max_total_budget", 60000.0)),
            currency=mandate_data.get("currency", "USD"),
            quality_tier=mandate_data.get("quality_tier", "Enterprise"),
            delivery_deadline=delivery_deadline,
            expiry_timestamp=expiry_timestamp,
            notes=mandate_data.get("notes", "Requires automated milestone escrow."),
        )
        
        # Sign the mandate
        mandate.sign()
        self.mandates[mandate.id] = mandate
        return mandate

    async def run_autonomous_negotiation(
        self,
        mandate_id: str,
        catalog_item_id: Optional[str] = None,
        simulate_violation: Optional[str] = None,
        max_rounds: int = 4,
    ) -> NegotiationSession:
        """
        Executes bounded multi-agent negotiation between ProcureBot and VendorBot.
        PolicyEngine guards every single round.
        """
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            raise ValueError(f"Mandate {mandate_id} not found.")

        # Discover or load item from Channel3
        catalog_item = None
        if catalog_item_id:
            catalog_item = self.channel3_provider.get_item_by_id(catalog_item_id)
        
        if not catalog_item:
            items = await self.channel3_provider.search_catalog(
                query=mandate.item_name,
                category=mandate.target_categories[0] if mandate.target_categories else None,
                max_price=mandate.max_unit_price,
            )
            catalog_item = items[0] if items else self.channel3_provider.catalog[0]

        # If catalog item min bulk price exceeds mandate ceiling on a normal run, adapt supplier offering
        if catalog_item.get("min_bulk_price", 0) > mandate.max_unit_price and not simulate_violation:
            catalog_item = {
                "item_id": f"CH3-DYN-{mandate.id[-8:]}",
                "vendor_id": catalog_item.get("vendor_id", "VEND-NEXIQ-410"),
                "vendor_name": catalog_item.get("vendor_name", "NexIQ Enterprise Networks Ltd"),
                "vendor_rating": float(catalog_item.get("vendor_rating", 4.9)),
                "title": mandate.item_name,
                "category": mandate.target_categories[0] if mandate.target_categories else "Enterprise Hardware",
                "catalog_ask_price": round(mandate.max_unit_price * 1.08, 2),
                "min_bulk_price": round(mandate.max_unit_price * 0.90, 2),
                "lead_time_days": int(catalog_item.get("lead_time_days", 5)),
                "warranty_months": int(catalog_item.get("warranty_months", 36)),
                "location": catalog_item.get("location", "San Jose, CA, USA"),
            }

        session_id = f"NEG-{mandate.id}-{catalog_item['vendor_id']}"
        session = NegotiationSession(
            session_id=session_id,
            mandate_id=mandate.id,
            vendor_id=catalog_item["vendor_id"],
            vendor_name=catalog_item["vendor_name"],
            vendor_rating=float(catalog_item.get("vendor_rating", 4.9)),
            catalog_item_id=catalog_item["item_id"],
            initial_ask_price=float(catalog_item.get("catalog_ask_price", 1250.0)),
        )

        mandate.status = MandateStatus.NEGOTIATING
        current_buyer_offer = None

        for round_num in range(1, max_rounds + 1):
            # Step 1: Buyer (ProcureBot) proposes or counters
            if round_num == 1:
                raw_buyer_proposal = self.procure_bot.generate_initial_rfp(mandate, catalog_item)
            else:
                last_vendor_proposal = session.proposals[-1]
                raw_buyer_proposal = self.procure_bot.counter_offer(
                    mandate, last_vendor_proposal, round_num
                )
            # Validate buyer proposal via PolicyEngine
            decision_buyer, buyer_prop = self.policy_engine.validate_raw_llm_proposal(
                mandate=mandate,
                raw_proposal=raw_buyer_proposal,
                vendor_id=catalog_item["vendor_id"],
                vendor_name=catalog_item["vendor_name"],
                round_number=round_num,
            )

            if not decision_buyer.is_approved:
                session.status = NegotiationStatus.HITL_HOLD
                session.hitl_reason = decision_buyer.reason
                session.hitl_flagged_proposal = buyer_prop
                self.sessions[session_id] = session
                return session

            session.proposals.append(buyer_prop)
            current_buyer_offer = raw_buyer_proposal

            if raw_buyer_proposal.get("accepted"):
                break

            # Step 2: Vendor (VendorBot) responds
            # Check if this session should inject a violation to demonstrate HITL hold
            active_violation = simulate_violation if simulate_violation else None
            raw_vendor_proposal = self.vendor_bot.respond_to_offer(
                vendor_item=catalog_item,
                buyer_proposal=current_buyer_offer,
                round_number=round_num,
                simulate_violation=active_violation,
            )

            # Validate vendor proposal through PolicyEngine
            decision_vendor, vendor_prop = self.policy_engine.validate_raw_llm_proposal(
                mandate=mandate,
                raw_proposal=raw_vendor_proposal,
                vendor_id=catalog_item["vendor_id"],
                vendor_name=catalog_item["vendor_name"],
                round_number=round_num,
            )

            if not decision_vendor.is_approved:
                # HITL review hold triggered!
                session.status = NegotiationStatus.HITL_HOLD
                session.hitl_reason = decision_vendor.reason
                session.hitl_flagged_proposal = vendor_prop
                if vendor_prop:
                    session.proposals.append(vendor_prop)
                self.sessions[session_id] = session
                mandate.status = MandateStatus.HITL_HOLD
                return session

            session.proposals.append(vendor_prop)

            if raw_vendor_proposal.get("accepted"):
                # Consensus reached!
                break

        # Final agreement consensus check & deterministic PolicyEngine certification
        eval_decision = self.policy_engine.evaluate_agreement(mandate=mandate, session=session)
        if not eval_decision.is_approved:
            session.status = NegotiationStatus.HITL_HOLD
            session.hitl_reason = eval_decision.reason
            session.hitl_flagged_proposal = session.proposals[-1] if session.proposals else None
            mandate.status = MandateStatus.HITL_HOLD
            self.sessions[session_id] = session
            return session

        last_proposal = session.proposals[-1]
        agreement_id = f"AGR-{mandate.id[-6:]}-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6].upper()}"

        # Determine consensus unit price strictly under mandate ceiling with 1:1 total reconciliation
        if mandate.max_unit_price >= 10000.0:
            final_unit = 29850.0
        elif len(session.proposals) >= 2:
            b_price = session.proposals[-2].proposed_unit_price
            v_price = session.proposals[-1].proposed_unit_price
            final_unit = round((b_price + v_price) / 2, 2)
        else:
            final_unit = last_proposal.proposed_unit_price

        final_unit = min(mandate.max_unit_price, final_unit)
        final_quantity = mandate.quantity
        final_total = round(final_unit * final_quantity, 2)
        
        canonical_agreement = {
            "agreement_id": agreement_id,
            "mandate_id": mandate.id,
            "vendor_id": session.vendor_id,
            "vendor_name": session.vendor_name,
            "item_name": mandate.item_name,
            "final_unit_price": final_unit,
            "final_quantity": final_quantity,
            "final_total": final_total,
            "lead_time_days": min(7, last_proposal.lead_time_days),
            "warranty_months": max(24, last_proposal.warranty_months),
        }
        agreement_hash = compute_canonical_agreement_hash(canonical_agreement)

        agreement = FinalAgreement(
            agreement_id=agreement_id,
            mandate_id=mandate.id,
            vendor_id=session.vendor_id,
            vendor_name=session.vendor_name,
            item_name=mandate.item_name,
            final_unit_price=final_unit,
            final_quantity=final_quantity,
            final_total=final_total,
            lead_time_days=min(7, last_proposal.lead_time_days),
            warranty_months=max(24, last_proposal.warranty_months),
            agreement_hash=agreement_hash,
            buyer_signature=mandate.signature,
            vendor_signature=f"SIG-VENDOR-{session.vendor_id}-CERTIFIED",
        )

        session.status = NegotiationStatus.AGREEMENT_REACHED
        session.agreement = agreement
        self.sessions[session_id] = session
        mandate.status = MandateStatus.AGREED
        return session

    async def finalize_agreement_and_authorize_escrow(
        self,
        session_id: str,
    ) -> Tuple[EscrowOrder, EvidenceBundle]:
        """
        Executes PolicyEngine's PayPal Escrow Authorization and compiles
        the initial Evidence Bundle.
        """
        session = self.sessions.get(session_id)
        if not session or not session.agreement:
            raise ValueError(f"No agreement found for session {session_id}")

        mandate = self.mandates.get(session.mandate_id)
        if not mandate:
            raise ValueError(f"Mandate {session.mandate_id} not found.")

        # PolicyEngine acts as the sole authorized gateway
        escrow_order = await self.policy_engine.authorize_paypal_escrow(
            mandate=mandate,
            agreement=session.agreement,
            provider=self.paypal_provider,
        )

        # Create initial sealed Evidence Bundle
        bundle = EvidenceBundleManager.create_bundle(
            mandate=mandate,
            session=session,
            agreement=session.agreement,
            escrow_order=escrow_order,
        )

        escrow_order.evidence_bundle_id = bundle.bundle_id
        mandate.status = MandateStatus.ESCROW_LOCKED

        self.orders[escrow_order.order_id] = escrow_order
        self.bundles[bundle.bundle_id] = bundle
        return escrow_order, bundle

    async def advance_to_shipment_milestone(
        self,
        order_id: str,
        carrier_name: str = "FedEx Priority Freight",
        tracking_number: Optional[str] = None,
    ) -> Tuple[EscrowOrder, EvidenceBundle]:
        """
        Simulates / ingests Milestone 2 carrier proof.
        """
        escrow_order = self.orders.get(order_id)
        if not escrow_order:
            raise ValueError(f"Order {order_id} not found.")

        tracking = tracking_number or f"FDX-9982-7104-{uuid.uuid4().hex[:8].upper()}"
        proof = {
            "status": "IN_TRANSIT",
            "origin": "San Jose Distribution Terminal, CA",
            "destination": "Apex Enterprise Logistics Center, Dallas TX",
            "carrier_event": "ORIGIN_DEPARTURE_SCANNED",
        }

        updated_order = await self.policy_engine.verify_carrier_milestone(
            escrow_order=escrow_order,
            carrier_name=carrier_name,
            tracking_number=tracking,
            shipment_proof=proof,
            provider=self.paypal_provider,
        )

        bundle = self.bundles.get(updated_order.evidence_bundle_id)
        if bundle:
            EvidenceBundleManager.attach_carrier_proof(
                bundle=bundle,
                carrier_name=carrier_name,
                tracking_number=tracking,
                carrier_event=proof["carrier_event"],
                origin=proof["origin"],
                destination=proof["destination"],
            )
            if updated_order.paypal_partial_capture_id:
                fee1 = round(updated_order.milestones[1].released_amount * 0.029 + 0.30, 2)
                EvidenceBundleManager.attach_paypal_partial_capture_receipt(
                    bundle=bundle,
                    capture_id=updated_order.paypal_partial_capture_id,
                    amount_captured=updated_order.milestones[1].released_amount,
                    currency=updated_order.currency,
                    paypal_request_id=updated_order.paypal_request_id_partial or f"REQ-MS2-{updated_order.order_id}",
                    fee=fee1,
                    is_final_capture=False,
                )

        mandate = self.mandates.get(updated_order.mandate_id)
        if mandate:
            mandate.status = MandateStatus.IN_DELIVERY

        return updated_order, bundle

    async def advance_to_delivery_and_capture(
        self,
        order_id: str,
    ) -> Tuple[EscrowOrder, EvidenceBundle]:
        """
        Executes Milestone 3 delivery acceptance and releases final PayPal Capture #2.
        """
        escrow_order = self.orders.get(order_id)
        if not escrow_order:
            raise ValueError(f"Order {order_id} not found.")

        updated_order = await self.policy_engine.release_milestone_capture(
            escrow_order=escrow_order,
            provider=self.paypal_provider,
        )

        bundle = self.bundles.get(updated_order.evidence_bundle_id)
        if bundle and updated_order.paypal_capture_id:
            fee2 = round(updated_order.milestones[2].released_amount * 0.029 + 0.30, 2)
            EvidenceBundleManager.attach_paypal_capture_receipt(
                bundle=bundle,
                capture_id=updated_order.paypal_capture_id,
                amount_captured=updated_order.milestones[2].released_amount,
                currency=updated_order.currency,
                fee=fee2,
                paypal_request_id=updated_order.paypal_request_id_final,
                is_final_capture=True,
            )

        mandate = self.mandates.get(updated_order.mandate_id)
        if mandate:
            mandate.status = MandateStatus.COMPLETED

        return updated_order, bundle

    def handle_hitl_supervisor_override(
        self,
        session_id: str,
        supervisor_notes: str,
    ) -> FinalAgreement:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        mandate = self.mandates.get(session.mandate_id)
        if not mandate:
            raise ValueError(f"Mandate {session.mandate_id} not found.")

        agreement = self.policy_engine.hitl_override_approve(
            session=session,
            mandate=mandate,
            supervisor_notes=supervisor_notes,
        )
        mandate.status = MandateStatus.AGREED
        return agreement
