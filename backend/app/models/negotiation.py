from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProposalSender(str, Enum):
    PROCURE_BOT = "ProcureBot"
    VENDOR_BOT = "VendorBot"
    HUMAN_SUPERVISOR = "HumanSupervisor"


class NegotiationStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AGREEMENT_REACHED = "AGREEMENT_REACHED"
    REJECTED = "REJECTED"
    HITL_HOLD = "HITL_HOLD"
    ESCALATED = "ESCALATED"


class NegotiationProposal(BaseModel):
    proposal_id: str
    round_number: int
    sender: ProposalSender
    mandate_id: str
    vendor_id: str
    vendor_name: str
    item_name: str
    proposed_unit_price: float
    proposed_quantity: int
    proposed_total: float
    lead_time_days: int
    warranty_months: int = 12
    rationale: str
    specifications_met: bool = True
    raw_llm_payload: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FinalAgreement(BaseModel):
    agreement_id: str
    mandate_id: str
    vendor_id: str
    vendor_name: str
    item_name: str
    final_unit_price: float
    final_quantity: int
    final_total: float
    lead_time_days: int
    warranty_months: int
    agreed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agreement_hash: str
    buyer_signature: Optional[str] = None
    vendor_signature: Optional[str] = None


class NegotiationSession(BaseModel):
    session_id: str
    mandate_id: str
    vendor_id: str
    vendor_name: str
    vendor_rating: float = 4.8
    catalog_item_id: str
    initial_ask_price: float
    status: NegotiationStatus = NegotiationStatus.IN_PROGRESS
    proposals: List[NegotiationProposal] = Field(default_factory=list)
    agreement: Optional[FinalAgreement] = None
    hitl_reason: Optional[str] = None
    hitl_flagged_proposal: Optional[NegotiationProposal] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
