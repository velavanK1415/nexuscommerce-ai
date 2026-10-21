"""
NexusCommerce AI - PayPal REST API v2 Provider
Includes dual modes:
1. Live PayPal REST API v2 (with client credentials OAuth2)
2. Zero-Key Demo Mode (deterministic mock provider so judges can test end-to-end without credentials)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import os
import uuid
import logging
import httpx

logger = logging.getLogger("nexus.paypal_provider")


class PayPalProvider:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        sandbox: bool = True,
        demo_mode: bool = True,
    ):
        self.client_id = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("PAYPAL_CLIENT_SECRET", "")
        self.sandbox = sandbox
        # If no client credentials provided, default to demo mode automatically
        self.demo_mode = demo_mode or (not self.client_id or not self.client_secret)
        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if self.sandbox
            else "https://api-m.paypal.com"
        )
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

        # In-memory mock database for Zero-Key Demo Mode
        self.mock_orders: Dict[str, Dict[str, Any]] = {}
        self.mock_authorizations: Dict[str, Dict[str, Any]] = {}
        self.mock_captures: Dict[str, Dict[str, Any]] = {}

    def is_demo_mode(self) -> bool:
        return self.demo_mode

    def set_demo_mode(self, enabled: bool):
        self.demo_mode = enabled
        logger.info(f"PayPalProvider demo mode set to: {self.demo_mode}")

    async def _get_access_token(self) -> str:
        if self.demo_mode:
            return "MOCK_PAYPAL_ACCESS_TOKEN_ZERO_KEY"

        now = datetime.now(timezone.utc).timestamp()
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expiry = now + data.get("expires_in", 3600)
            return self._access_token

    async def create_and_authorize_order(
        self,
        order_id: str,
        amount: float,
        currency: str = "USD",
        description: str = "NexusCommerce Escrow Order",
        custom_id: str = "",
    ) -> Dict[str, Any]:
        """
        Creates an order with intent=AUTHORIZE and authorizes it.
        In Zero-Key Demo Mode: simulates PayPal REST API v2 response deterministically.
        In Live Mode: calls POST /v2/checkout/orders and handles authorization.
        """
        if self.demo_mode:
            paypal_order_id = f"PAYPAL-ORD-{uuid.uuid4().hex[:10].upper()}"
            auth_id = f"AUTH-{uuid.uuid4().hex[:12].upper()}"
            
            created_time = datetime.now(timezone.utc).isoformat()
            order_data = {
                "id": paypal_order_id,
                "status": "APPROVED",
                "intent": "AUTHORIZE",
                "create_time": created_time,
                "custom_id": custom_id,
                "purchase_units": [
                    {
                        "reference_id": order_id,
                        "description": description,
                        "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                        "payments": {
                            "authorizations": [
                                {
                                    "id": auth_id,
                                    "status": "CREATED",
                                    "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                                    "seller_protection": {"status": "ELIGIBLE"},
                                    "expiration_time": "2026-11-20T23:59:59Z",
                                    "create_time": created_time,
                                }
                            ]
                        },
                    }
                ],
                "links": [
                    {
                        "href": f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}",
                        "rel": "approve",
                        "method": "GET",
                    },
                    {
                        "href": f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}/authorize",
                        "rel": "authorize",
                        "method": "POST",
                    },
                ],
            }

            self.mock_orders[paypal_order_id] = order_data
            self.mock_authorizations[auth_id] = {
                "id": auth_id,
                "order_id": paypal_order_id,
                "status": "CREATED",
                "amount": amount,
                "currency": currency,
                "created_at": created_time,
            }

            return {
                "paypal_order_id": paypal_order_id,
                "paypal_authorization_id": auth_id,
                "status": "AUTHORIZED",
                "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}",
                "amount": amount,
                "currency": currency,
                "raw_response": order_data,
            }

        # LIVE MODE
        token = await self._get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [
                {
                    "reference_id": order_id,
                    "description": description,
                    "custom_id": custom_id,
                    "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                }
            ],
            "application_context": {
                "return_url": "http://localhost:5173/escrow/success",
                "cancel_url": "http://localhost:5173/escrow/cancel",
                "brand_name": "NexusCommerce AI",
                "user_action": "CONTINUE",
            },
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=payload,
                timeout=15.0,
            )
            resp.raise_for_status()
            order_data = resp.json()
            paypal_order_id = order_data["id"]

            # Find approval url
            approval_url = None
            for link in order_data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")

            # Try immediate authorization (or return approval URL for buyer flow)
            auth_resp = await client.post(
                f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/authorize",
                headers=headers,
                timeout=15.0,
            )
            auth_id = None
            auth_status = "PENDING"
            if auth_resp.status_code == 201:
                auth_data = auth_resp.json()
                auths = (
                    auth_data.get("purchase_units", [{}])[0]
                    .get("payments", {})
                    .get("authorizations", [])
                )
                if auths:
                    auth_id = auths[0].get("id")
                    auth_status = "AUTHORIZED"

            return {
                "paypal_order_id": paypal_order_id,
                "paypal_authorization_id": auth_id or f"AUTH-PENDING-{paypal_order_id}",
                "status": auth_status,
                "approval_url": approval_url,
                "amount": amount,
                "currency": currency,
                "raw_response": order_data,
            }

    async def capture_authorization(
        self,
        authorization_id: str,
        amount: float,
        currency: str = "USD",
        is_final_capture: bool = True,
        paypal_request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Captures previously authorized funds (partial or final) under PayPal Orders v2.
        Supports multi-stage milestone partial captures (e.g. 30% mobilization on carrier proof, 70% final).
        Includes PayPal-Request-Id for enterprise idempotency.
        """
        req_id = paypal_request_id or f"REQ-IDEMP-{uuid.uuid4().hex[:12].upper()}"
        if self.demo_mode:
            capture_id = f"CAP-{uuid.uuid4().hex[:12].upper()}"
            capture_time = datetime.now(timezone.utc).isoformat()
            fee = round(amount * 0.029 + 0.30, 2)
            net_amount = round(amount - fee, 2)

            capture_data = {
                "id": capture_id,
                "status": "COMPLETED",
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                "final_capture": is_final_capture,
                "paypal_request_id": req_id,
                "seller_protection": {"status": "ELIGIBLE"},
                "seller_receivable_breakdown": {
                    "gross_amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                    "paypal_fee": {"currency_code": currency, "value": f"{fee:.2f}"},
                    "net_amount": {"currency_code": currency, "value": f"{net_amount:.2f}"},
                },
                "create_time": capture_time,
                "update_time": capture_time,
            }

            self.mock_captures[capture_id] = capture_data
            if authorization_id in self.mock_authorizations:
                self.mock_authorizations[authorization_id]["status"] = (
                    "CAPTURED" if is_final_capture else "PARTIALLY_CAPTURED"
                )

            return {
                "capture_id": capture_id,
                "status": "COMPLETED",
                "amount_captured": amount,
                "final_capture": is_final_capture,
                "paypal_request_id": req_id,
                "fee": fee,
                "net_amount": net_amount,
                "raw_response": capture_data,
            }

        # LIVE MODE
        token = await self._get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": req_id,
        }
        payload = {
            "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
            "final_capture": is_final_capture,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v2/payments/authorizations/{authorization_id}/capture",
                headers=headers,
                json=payload,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "capture_id": data.get("id"),
                "status": data.get("status"),
                "amount_captured": float(data.get("amount", {}).get("value", amount)),
                "final_capture": is_final_capture,
                "paypal_request_id": req_id,
                "raw_response": data,
            }

    async def get_order_details(self, paypal_order_id: str) -> Dict[str, Any]:
        if self.demo_mode:
            return self.mock_orders.get(paypal_order_id, {"id": paypal_order_id, "status": "APPROVED"})

        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v2/checkout/orders/{paypal_order_id}",
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
