"""Broker execution adapter interface (LIVE side of the PAPER/LIVE separation).

The paper engine (``paper_engine.py``) is the source of truth for the user's
book: it decides fills, cash and positions. A ``BrokerAdapter`` is the seam
through which a future *live execution* mode would place real orders at a
broker. The paper engine never calls a broker order API; only an explicit
live path may, and it must keep the paper ledger authoritative for the user.

Adapter contract:
- ``place_order``  — submit a new order, return the broker-side id + status.
- ``cancel_order`` — cancel an open broker order by id.
- ``get_order_status`` — poll a broker order's current state by id.

Every adapter exposes ``name`` and ``is_mock`` so callers can surface whether
an execution went to a real broker or a simulator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.domain.enums import OrderSide, OrderType


class BrokerAPIError(Exception):
    """Raised when a broker order API cannot be reached or returns an error."""


@dataclass
class BrokerOrderRequest:
    """The minimal data needed to place an order at a broker."""

    symbol: str
    exchange: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Decimal | None = None


@dataclass
class BrokerOrderResult:
    """Result of a broker-side order operation."""

    broker_order_id: str
    status: str
    filled_quantity: int | None = None
    avg_fill_price: Decimal | None = None
    raw: dict[str, Any] | None = None


class BrokerAdapter(ABC):
    """Place, cancel and query orders against a broker execution backend."""

    name: str = "base"
    is_mock: bool = True

    @abstractmethod
    async def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult:
        """Submit an order; returns the broker-side order reference."""
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        """Cancel an open broker order; idempotent on already-final orders."""
        raise NotImplementedError

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> BrokerOrderResult:
        """Return the current broker-side state of an order."""
        raise NotImplementedError


class MockBrokerAdapter(BrokerAdapter):
    """Deterministic in-process broker simulator.

    ``is_mock = True`` — nothing leaves this process. MARKET orders fill
    immediately; LIMIT orders rest as ``pending`` until explicitly cancelled
    (there is no market feed to cross them). Exists so the live-execution
    seam can be exercised end-to-end without touching a real broker.
    """

    name = "mock"
    is_mock = True

    def __init__(self) -> None:
        self._orders: dict[str, BrokerOrderResult] = {}

    def _record(self, result: BrokerOrderResult) -> None:
        self._orders[result.broker_order_id] = result

    async def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult:
        from uuid import uuid4

        broker_order_id = f"mock-{uuid4().hex}"
        if request.order_type == OrderType.MARKET:
            result = BrokerOrderResult(
                broker_order_id=broker_order_id,
                status="filled",
                filled_quantity=request.quantity,
                avg_fill_price=request.limit_price,
                raw={"simulated": True},
            )
        else:
            result = BrokerOrderResult(
                broker_order_id=broker_order_id,
                status="pending",
                raw={"simulated": True},
            )
        self._record(result)
        return result

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        existing = self._orders.get(broker_order_id)
        if existing is None:
            raise BrokerAPIError(f"Order {broker_order_id} not found.")
        if existing.status != "pending":
            raise BrokerAPIError(f"Order {broker_order_id} is not cancellable.")
        result = BrokerOrderResult(
            broker_order_id=broker_order_id,
            status="cancelled",
            raw={"simulated": True},
        )
        self._record(result)
        return result

    async def get_order_status(self, broker_order_id: str) -> BrokerOrderResult:
        existing = self._orders.get(broker_order_id)
        if existing is None:
            raise BrokerAPIError(f"Order {broker_order_id} not found.")
        return existing
