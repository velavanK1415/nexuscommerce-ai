from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import hashlib
import json


class EvidenceBundle(BaseModel):
    bundle_id: str
    order_id: str
    mandate_id: str
    agreement_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # 1. Signed Mandate Snapshot
    mandate_snapshot: Dict[str, Any]
    
    # 2. Agent Negotiation Transcript
    negotiation_transcript: List[Dict[str, Any]]
    
    # 3. Agreement & Agreement Hash
    agreement_payload: Dict[str, Any]
    agreement_hash: str
    
    # 4. PayPal Authorization Record
    paypal_authorization_receipt: Optional[Dict[str, Any]] = None
    
    # 5. Carrier Shipment & Delivery Proof
    carrier_proof: Optional[Dict[str, Any]] = None
    
    # 6. PayPal Partial Capture Receipt (Milestone 2 - 30% Mobilization)
    paypal_partial_capture_receipt: Optional[Dict[str, Any]] = None

    # 7. PayPal Final Capture Receipt (Milestone 3 - 70% Final Settlement)
    paypal_capture_receipt: Optional[Dict[str, Any]] = None
    
    # 8. Mandate vs Order Diff & Invariant Audit
    mandate_diff: Optional[Dict[str, Any]] = None

    # Tamper-evident root hash
    bundle_root_hash: str = ""
    tamper_evident_valid: bool = True
    audit_chain: List[str] = Field(default_factory=list)

    def calculate_root_hash(self) -> str:
        """
        Computes a cryptographic Merkle-style root hash across all constituent audit items.
        If ANY byte in agreement_payload, mandate_snapshot, or receipt is modified,
        bundle_root_hash changes immediately.
        """
        # Canonical leaf hashes
        mandate_leaf = hashlib.sha256(
            json.dumps(self.mandate_snapshot, sort_keys=True).encode("utf-8")
        ).hexdigest()

        agreement_leaf = hashlib.sha256(
            json.dumps(self.agreement_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        transcript_leaf = hashlib.sha256(
            json.dumps(self.negotiation_transcript, sort_keys=True).encode("utf-8")
        ).hexdigest()

        auth_leaf = hashlib.sha256(
            json.dumps(self.paypal_authorization_receipt or {}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        carrier_leaf = hashlib.sha256(
            json.dumps(self.carrier_proof or {}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        partial_capture_leaf = hashlib.sha256(
            json.dumps(self.paypal_partial_capture_receipt or {}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        capture_leaf = hashlib.sha256(
            json.dumps(self.paypal_capture_receipt or {}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        canonical_dict = {
            "bundle_id": self.bundle_id,
            "order_id": self.order_id,
            "mandate_id": self.mandate_id,
            "mandate_leaf": mandate_leaf,
            "agreement_leaf": agreement_leaf,
            "transcript_leaf": transcript_leaf,
            "auth_leaf": auth_leaf,
            "carrier_leaf": carrier_leaf,
            "partial_capture_leaf": partial_capture_leaf,
            "capture_leaf": capture_leaf,
        }
        raw_bytes = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def seal_bundle(self) -> str:
        self.bundle_root_hash = self.calculate_root_hash()
        self.audit_chain.append(
            f"SEALED_AT_{datetime.now(timezone.utc).isoformat()}_HASH_{self.bundle_root_hash}"
        )
        self.tamper_evident_valid = True
        return self.bundle_root_hash

    def verify_integrity(self) -> bool:
        expected = self.calculate_root_hash()
        is_valid = (self.bundle_root_hash == expected)
        self.tamper_evident_valid = is_valid
        return is_valid
