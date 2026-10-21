from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EscrowStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    AUTHORIZATION_PENDING = "AUTHORIZATION_PENDING"
    FUNDS_AUTHORIZED = "FUNDS_AUTHORIZED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FUNDS_CAPTURED = "FUNDS_CAPTURED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"
    HITL_HOLD = "HITL_HOLD"


class MilestoneStepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EscrowMilestone(BaseModel):
    milestone_id: str
    sequence: int
    name: str
    description: str
    status: MilestoneStepStatus = MilestoneStepStatus.PENDING
    payout_percentage: float = 0.0  # percentage of total funds disbursed at this step
    allocated_amount: float
    released_amount: float = 0.0
    paypal_reference_id: Optional[str] = None
    paypal_request_id: Optional[str] = None  # Idempotency key for PayPal capture
    is_final_capture: Optional[bool] = None
    evidence_required: str
    evidence_submitted: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None


class EscrowOrder(BaseModel):
    order_id: str
    mandate_id: str
    agreement_id: str
    vendor_id: str
    vendor_name: str
    item_name: str
    quantity: int
    unit_price: float
    total_amount: float
    currency: str = "USD"
    status: EscrowStatus = EscrowStatus.INITIALIZED
    paypal_order_id: Optional[str] = None
    paypal_authorization_id: Optional[str] = None
    paypal_partial_capture_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    paypal_request_id_partial: Optional[str] = None
    paypal_request_id_final: Optional[str] = None
    total_released: float = 0.0
    catalog_ask_price: Optional[float] = None
    negotiated_alpha: Optional[float] = None
    budget_headroom: Optional[float] = None
    paypal_approval_url: Optional[str] = None
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier_status: Optional[str] = None
    milestones: List[EscrowMilestone] = Field(default_factory=list)
    evidence_bundle_id: Optional[str] = None
    hitl_flag: bool = False
    hitl_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

