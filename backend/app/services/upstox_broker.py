"""Upstox v2 REST order-placement adapter (LIVE side).

Implements the ``BrokerAdapter`` contract against the Upstox v2 order API:
``POST /order/place``, ``DELETE /order/cancel`` and ``GET /order/details``.
``is_mock = False`` and ``name = "upstox"`` — any consumer can see this is a
real-broker adapter.

This is deliberately **not** wired into the paper engine: the paper ledger
stays the source of truth for the user. This adapter is the execution seam a
future live mode would call, and it must never be reached from
``paper_engine.py``.

Note on ``instrument_token``: Upstox order placement keys instruments by a
token rather than a symbol string. This adapter forwards the exchange:SYMBOL
key (the same form the quote endpoint accepts); wiring against a specific
broker account may require resolving the account-scoped numeric token from
the instrument master.
"""

import logging
from decimal import Decimal
from typing import Any

import httpx

from app.services.broker import (
    BrokerAdapter,
    BrokerAPIError,
    BrokerOrderRequest,
    BrokerOrderResult,
)

logger = logging.getLogger(__name__)

_UPSTOX_STATUS_TO_ORDER_STATUS = {
    "complete": "filled",
    "cancelled": "cancelled",
    "rejected": "rejected",
    "pending": "pending",
    "open": "open",
    "partially_filled": "partially_filled",
}


def _map_status(upstox_status: str) -> str:
    return _UPSTOX_STATUS_TO_ORDER_STATUS.get(upstox_status.lower(), upstox_status.lower())


class UpstoxBrokerAdapter(BrokerAdapter):
    """Real-broker order placement via Upstox v2 REST endpoints."""

    name = "upstox"
    is_mock = False

    def __init__(
        self,
        *,
        api_key: str,
        access_token: str,
        base_url: str = "https://api.upstox.com/v2",
        timeout: float = 5.0,
        product: str = "D",
        validity: str = "DAY",
    ) -> None:
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.product = product
        self.validity = validity

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def _instrument_token(self, request: BrokerOrderRequest) -> str:
        return f"{request.exchange}:{request.symbol}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                call = getattr(client, method.lower())
                kwargs: dict[str, Any] = {"params": params, "headers": self._headers()}
                if json is not None:
                    kwargs["json"] = json
                resp = await call(f"{self.base_url}{path}", **kwargs)
        except httpx.HTTPError as exc:
            raise BrokerAPIError(f"Upstox order API request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise BrokerAPIError(
                f"Upstox order API returned HTTP {resp.status_code}: {resp.text[:200]}"
            )
        body = resp.json()
        if body.get("status") != "success":
            raise BrokerAPIError(f"Upstox order API error: {body.get('errors') or body}")
        return body.get("data") or {}

    async def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult:
        payload: dict[str, Any] = {
            "product": self.product,
            "instrument_token": self._instrument_token(request),
            "order_type": request.order_type.value,
            "quantity": request.quantity,
            "price": "0",
            "validity": self.validity,
            "is_amo": False,
        }
        if request.order_type.value == "LIMIT":
            if request.limit_price is None:
                raise BrokerAPIError("LIMIT order requires a limit price.")
            payload["price"] = str(request.limit_price)
        data = await self._request("POST", "/order/place", json=payload)
        order_id = str(data.get("order_id") or "")
        if not order_id:
            raise BrokerAPIError(f"Upstox place-order returned no order_id: {data}")
        logger.info("upstox order placed: broker_order_id=%s", order_id)
        return BrokerOrderResult(broker_order_id=order_id, status="pending", raw=data)

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        data = await self._request(
            "DELETE",
            "/order/cancel",
            json={"order_id": broker_order_id, "variety": "regular"},
        )
        logger.info("upstox order cancel requested: broker_order_id=%s", broker_order_id)
        return BrokerOrderResult(broker_order_id=broker_order_id, status="cancelled", raw=data)

    async def get_order_status(self, broker_order_id: str) -> BrokerOrderResult:
        data = await self._request(
            "GET",
            "/order/details",
            params={"order_id": broker_order_id},
        )
        status = _map_status(str(data.get("status") or "open"))
        filled = data.get("filled_quantity")
        avg = data.get("average_price")
        return BrokerOrderResult(
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=int(filled) if filled is not None else None,
            avg_fill_price=Decimal(str(avg)) if avg is not None else None,
            raw=data,
        )
