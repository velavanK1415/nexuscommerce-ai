from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import hashlib
import json


class MandateStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    NEGOTIATING = "NEGOTIATING"
    AGREED = "AGREED"
    ESCROW_LOCKED = "ESCROW_LOCKED"
    IN_DELIVERY = "IN_DELIVERY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    HITL_HOLD = "HITL_HOLD"


class QualityTier(str, Enum):
    ENTERPRISE = "Enterprise"
    STANDARD = "Standard"
    ECONOMY = "Economy"


class ProcurementMandate(BaseModel):
    id: str = Field(..., description="Unique mandate identifier, e.g. MAN-2026-001")
    buyer_id: str = Field(..., description="Buyer company or user ID")
    buyer_name: str = Field(..., description="Organization or buyer name")
    buyer_email: str = Field(..., description="Buyer contact email for notifications")
    title: str = Field(..., description="Title of the procurement mandate")
    target_categories: List[str] = Field(default_factory=list, description="Allowed merchandise/service categories")
    item_name: str = Field(..., description="Specific item or service requested")
    quantity: int = Field(..., gt=0, description="Exact quantity required")
    max_unit_price: float = Field(..., gt=0.0, description="Strict price ceiling per unit in USD")
    max_total_budget: float = Field(..., gt=0.0, description="Strict total budget ceiling in USD")
    currency: str = Field(default="USD", description="Currency ISO code")
    quality_tier: QualityTier = Field(default=QualityTier.ENTERPRISE, description="Minimum quality grade")
    delivery_deadline: str = Field(..., description="Max acceptable delivery ISO timestamp")
    expiry_timestamp: str = Field(..., description="Mandate expiration ISO timestamp")
    milestones_required: List[str] = Field(
        default_factory=lambda: [
            "1. Escrow Authorization",
            "2. Carrier Shipment Proof",
            "3. Delivery Verification & Escrow Release",
        ],
        description="Required escrow milestone checkpoints",
    )
    status: MandateStatus = Field(default=MandateStatus.ACTIVE)
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature: Optional[str] = None

    def compute_signature_payload(self) -> str:
        payload = {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "max_unit_price": self.max_unit_price,
            "max_total_budget": self.max_total_budget,
            "delivery_deadline": self.delivery_deadline,
            "expiry_timestamp": self.expiry_timestamp,
        }
        return json.dumps(payload, sort_keys=True)

    def sign(self, secret: str = "nexus-tamper-proof-secret-2026") -> str:
        payload = self.compute_signature_payload()
        sig = hashlib.sha256(f"{payload}:{secret}".encode("utf-8")).hexdigest()
        self.signature = sig
        return sig

    def verify_signature(self, secret: str = "nexus-tamper-proof-secret-2026") -> bool:
        if not self.signature:
            return False
        payload = self.compute_signature_payload()
        expected = hashlib.sha256(f"{payload}:{secret}".encode("utf-8")).hexdigest()
        return self.signature == expected

    @staticmethod
    def verify_snapshot_signature(snapshot: Dict[str, Any], secret: str = "nexus-tamper-proof-secret-2026") -> bool:
        sig = snapshot.get("signature")
        if not sig:
            return False
        payload = {
            "id": snapshot.get("id"),
            "buyer_id": snapshot.get("buyer_id"),
            "item_name": snapshot.get("item_name"),
            "quantity": snapshot.get("quantity"),
            "max_unit_price": snapshot.get("max_unit_price"),
            "max_total_budget": snapshot.get("max_total_budget"),
            "delivery_deadline": snapshot.get("delivery_deadline"),
            "expiry_timestamp": snapshot.get("expiry_timestamp"),
        }
        raw = json.dumps(payload, sort_keys=True)
        expected = hashlib.sha256(f"{raw}:{secret}".encode("utf-8")).hexdigest()
        return sig == expected

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expiry_timestamp.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False


class MandateCreateRequest(BaseModel):
    buyer_id: str = "BUYER-CORP-9021"
    buyer_name: str = "Apex Global Logistics Corp"
    buyer_email: str = "procurement@apexlogistics.io"
    title: str = "High-Density Data Center Edge Routers"
    target_categories: List[str] = ["Networking Hardware", "Data Center Equipment", "Edge Infrastructure"]
    item_name: str = "NexusEdge Pro 100G Router"
    quantity: int = 50
    max_unit_price: float = 1200.0
    max_total_budget: float = 60000.0
    currency: str = "USD"
    quality_tier: QualityTier = QualityTier.ENTERPRISE
    delivery_deadline: Optional[str] = None
    expiry_timestamp: Optional[str] = None
    notes: Optional[str] = "Requires enterprise redundancy and carrier tracking for release."
