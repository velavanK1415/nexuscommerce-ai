import pytest
from datetime import datetime, timezone, timedelta
from app.models.mandate import ProcurementMandate, MandateStatus, QualityTier


def test_mandate_creation_and_signature():
    now = datetime.now(timezone.utc)
    delivery_deadline = (now + timedelta(days=30)).isoformat()
    expiry_timestamp = (now + timedelta(days=14)).isoformat()

    mandate = ProcurementMandate(
        id="MAN-TEST-001",
        buyer_id="BUYER-CORP-9021",
        buyer_name="Apex Global Logistics",
        buyer_email="procure@apex.io",
        title="Edge Hardware Sourcing",
        target_categories=["Networking Hardware"],
        item_name="NexusEdge Pro 100G",
        quantity=50,
        max_unit_price=1200.0,
        max_total_budget=60000.0,
        quality_tier=QualityTier.ENTERPRISE,
        delivery_deadline=delivery_deadline,
        expiry_timestamp=expiry_timestamp,
    )

    sig = mandate.sign()
    assert sig is not None
    assert len(sig) == 64  # SHA-256 hex string
    assert mandate.signature == sig
    assert not mandate.is_expired()


def test_mandate_expiry_detection():
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    mandate = ProcurementMandate(
        id="MAN-EXPIRED-001",
        buyer_id="BUYER-01",
        buyer_name="Old Buyer",
        buyer_email="old@buyer.com",
        title="Expired mandate",
        target_categories=["Hardware"],
        item_name="Old Switch",
        quantity=10,
        max_unit_price=500.0,
        max_total_budget=5000.0,
        delivery_deadline=past,
        expiry_timestamp=past,
    )
    assert mandate.is_expired() is True
