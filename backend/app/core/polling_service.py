"""
NexusCommerce AI - Polling Fallback Service
Fulfills Architectural Requirement 4: 'Webhooks first, polling fallback'
If a PayPal webhook notification is delayed or dropped over the network,
this fallback reconciles order and authorization states directly against PayPal REST API v2.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import asyncio
import logging

from app.models.escrow import EscrowOrder, EscrowStatus, MilestoneStepStatus
from app.providers.paypal_provider import PayPalProvider

logger = logging.getLogger("nexus.polling_service")


class PollingFallbackService:
    def __init__(self, paypal_provider: PayPalProvider, orders_store: Dict[str, EscrowOrder]):
        self.paypal_provider = paypal_provider
        self.orders = orders_store
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.poll_log: List[Dict[str, Any]] = []

    async def start_background_polling(self, interval_seconds: int = 15):
        """Starts periodic fallback polling in background."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop(interval_seconds))
        logger.info(f"Background polling fallback started (interval: {interval_seconds}s)")

    async def _poll_loop(self, interval_seconds: int):
        while self.is_running:
            try:
                await self.reconcile_all_active()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling fallback loop: {e}")
            await asyncio.sleep(interval_seconds)

    def stop_background_polling(self):
        """Stops background polling task."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Background polling fallback stopped.")

    async def reconcile_order(self, order_id: str) -> Dict[str, Any]:
        """
        Manually or periodically checks PayPal API for the current order state.
        Handles both authorization and capture states.
        """
        escrow_order = self.orders.get(order_id)
        if not escrow_order or not escrow_order.paypal_order_id:
            return {"status": "SKIPPED", "reason": "No order or PayPal order ID found."}

        try:
            order_data = await self.paypal_provider.get_order_details(escrow_order.paypal_order_id)
            paypal_status = order_data.get("status")

            reconciled = False
            # 1. Reconcile Authorization hold
            if paypal_status in ["APPROVED", "COMPLETED", "AUTHORIZED"] and escrow_order.status == EscrowStatus.AUTHORIZATION_PENDING:
                escrow_order.status = EscrowStatus.FUNDS_AUTHORIZED
                if escrow_order.milestones:
                    escrow_order.milestones[0].status = MilestoneStepStatus.COMPLETED
                    escrow_order.milestones[0].completed_at = datetime.now(timezone.utc).isoformat()
                    if len(escrow_order.milestones) > 1 and escrow_order.milestones[1].status == MilestoneStepStatus.PENDING:
                        escrow_order.milestones[1].status = MilestoneStepStatus.IN_PROGRESS
                escrow_order.updated_at = datetime.now(timezone.utc).isoformat()
                reconciled = True

            # 2. Reconcile Capture completion if PayPal marked completed while in transit
            elif paypal_status in ["COMPLETED", "CAPTURED"] and escrow_order.status == EscrowStatus.IN_TRANSIT:
                escrow_order.status = EscrowStatus.COMPLETED
                escrow_order.carrier_status = "DELIVERED"
                if not escrow_order.paypal_capture_id:
                    escrow_order.paypal_capture_id = f"CAP-POLL-{escrow_order.order_id[-6:]}"
                if len(escrow_order.milestones) > 2:
                    escrow_order.milestones[2].status = MilestoneStepStatus.COMPLETED
                    escrow_order.milestones[2].completed_at = datetime.now(timezone.utc).isoformat()
                    escrow_order.milestones[2].released_amount = escrow_order.total_amount
                    escrow_order.milestones[2].paypal_reference_id = escrow_order.paypal_capture_id
                escrow_order.updated_at = datetime.now(timezone.utc).isoformat()
                reconciled = True

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "order_id": order_id,
                "paypal_order_id": escrow_order.paypal_order_id,
                "paypal_status": paypal_status,
                "reconciled": reconciled,
            }
            self.poll_log.append(log_entry)
            return log_entry
        except Exception as e:
            logger.error(f"Polling reconciliation failed for order {order_id}: {e}")
            return {"status": "ERROR", "error": str(e)}

    async def reconcile_all_active(self) -> List[Dict[str, Any]]:
        results = []
        for order_id, order in list(self.orders.items()):
            if order.status in [EscrowStatus.AUTHORIZATION_PENDING, EscrowStatus.FUNDS_AUTHORIZED, EscrowStatus.IN_TRANSIT]:
                res = await self.reconcile_order(order_id)
                results.append(res)
        return results
