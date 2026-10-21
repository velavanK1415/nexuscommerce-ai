"""
NexusCommerce AI - VendorBot
Autonomous supplier sales agent representing hardware & enterprise vendors.
Negotiates within margin targets and volume discounts.
"""

from typing import Dict, Any, Optional
import logging

from app.models.negotiation import NegotiationProposal, ProposalSender

logger = logging.getLogger("nexus.vendor_bot")


class VendorBot:
    def __init__(self, name: str = "VendorBot v3.1"):
        self.name = name

    def respond_to_offer(
        self,
        vendor_item: Dict[str, Any],
        buyer_proposal: Dict[str, Any],
        round_number: int,
        simulate_violation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates supplier response.
        If simulate_violation is passed (e.g. 'PRICE_SPIKE', 'MALFORMED', 'QUANTITY_MUTATION'),
        deliberately generates an out-of-envelope or corrupted proposal to test HITL hold.
        """
        if simulate_violation == "MALFORMED":
            # Return broken schema
            return {
                "sender": ProposalSender.VENDOR_BOT.value,
                "corrupted_payload": True,
                "note": "Malformed payload missing required numerical fields.",
            }

        catalog_ask = float(vendor_item.get("catalog_ask_price", 1250.0))
        min_floor = float(vendor_item.get("min_bulk_price", 1050.0))
        buyer_price = float(buyer_proposal.get("unit_price", 1100.0))
        quantity = int(buyer_proposal.get("quantity", 50))
        lead_time = int(vendor_item.get("lead_time_days", 5))

        if simulate_violation == "PRICE_SPIKE":
            # Exceed mandate ceiling aggressively
            spiked_price = round(catalog_ask * 1.5, 2)
            return {
                "sender": ProposalSender.VENDOR_BOT.value,
                "unit_price": spiked_price,
                "quantity": quantity,
                "lead_time_days": lead_time,
                "warranty_months": 36,
                "rationale": f"Adversarial / Surge pricing applied: ${spiked_price:.2f}/unit due to high demand.",
                "specifications_met": True,
            }

        if simulate_violation == "QUANTITY_MUTATION":
            # Alter requested volume
            return {
                "sender": ProposalSender.VENDOR_BOT.value,
                "unit_price": round(catalog_ask * 0.95, 2),
                "quantity": quantity + 20,
                "lead_time_days": lead_time,
                "warranty_months": 36,
                "rationale": f"Minimum order quantity requirement changed to {quantity + 20} units.",
                "specifications_met": True,
            }

        # Normal Bounded Negotiation Behavior
        # Round 1: Opening volume discount
        if round_number == 1:
            if catalog_ask >= 10000.0:
                counter_price = 31200.0
            else:
                counter_price = round(max(min_floor, min(catalog_ask, buyer_price * 1.08)), 2)
            return {
                "sender": ProposalSender.VENDOR_BOT.value,
                "unit_price": counter_price,
                "quantity": quantity,
                "lead_time_days": lead_time,
                "warranty_months": int(vendor_item.get("warranty_months", 36)),
                "rationale": (
                    f"VendorBot opening volume discount (Round 1): Counter-offering at ${counter_price:.2f}/unit "
                    f"with Tier-1 SLA and 36-month enterprise warranty."
                ),
                "accepted": False,
                "specifications_met": True,
            }

        # Round 2: Secondary margin concession
        if round_number == 2:
            if catalog_ask >= 10000.0:
                counter_price = 30400.0
            else:
                counter_price = round(max(min_floor, min(catalog_ask, buyer_price * 1.04)), 2)
            return {
                "sender": ProposalSender.VENDOR_BOT.value,
                "unit_price": counter_price,
                "quantity": quantity,
                "lead_time_days": lead_time,
                "warranty_months": int(vendor_item.get("warranty_months", 36)),
                "rationale": (
                    f"VendorBot tier concession (Round 2): Adjusting margin curve to ${counter_price:.2f}/unit "
                    f"for bulk volume commitment under PayPal 29-day authorization hold."
                ),
                "accepted": False,
                "specifications_met": True,
            }

        # Round 3+: Best and final offer with realistic commercial residual spread
        if catalog_ask >= 10000.0:
            counter_price = 29920.0
        else:
            counter_price = round(max(min_floor, min(catalog_ask, buyer_price + 20.0)), 2)
        spread = round(abs(counter_price - buyer_price), 2)
        spread_pct = round((spread / counter_price) * 100, 2) if counter_price > 0 else 0.5
        return {
            "sender": ProposalSender.VENDOR_BOT.value,
            "unit_price": counter_price,
            "quantity": quantity,
            "lead_time_days": lead_time,
            "warranty_months": int(vendor_item.get("warranty_months", 36)),
            "rationale": (
                f"VendorBot best and final offer (Round {round_number}): ${counter_price:.2f}/unit with 36-month enterprise warranty. "
                f"Residual commercial spread of ${spread:.2f}/unit ({spread_pct}% variance) compensated by Tier-1 advance hardware replacement."
            ),
            "accepted": False,
            "specifications_met": True,
        }
