"""Live execution path — routes orders to a real broker via a BrokerAdapter.

PAPER/LIVE separation: ``paper_engine.py`` never calls a broker. This service
is the LIVE side of that seam: it sends orders through a ``BrokerAdapter``
and then books the broker-reported fills into the **paper ledger** (cash,
positions, trades), so the user's displayed book stays the source of truth
for them while the broker is the execution backend.

A portfolio must be in ``execution_mode = "live"`` and live execution must be
enabled (``LIVE_EXECUTION_ENABLED``) before any order reaches this service.
"""

import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utcnow
from app.domain.enums import ExecutionMode, OrderSide, OrderStatus
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.repositories.instruments import InstrumentRepository
from app.repositories.orders import OrderRepository
from app.repositories.positions import PositionRepository
from app.repositories.trades import TradeRepository
from app.schemas.order import OrderCreate
from app.services.broker import BrokerAdapter, BrokerOrderRequest
from app.services.paper_engine import _apply_fill, _round_price

logger = logging.getLogger(__name__)

_BROKER_TO_PAPER_STATUS = {
    "filled": OrderStatus.FILLED.value,
    "partially_filled": OrderStatus.PARTIALLY_FILLED.value,
    "pending": OrderStatus.PENDING.value,
    "open": OrderStatus.PENDING.value,
    "cancelled": OrderStatus.CANCELLED.value,
    "rejected": OrderStatus.REJECTED.value,
}


def _map_broker_status(broker_status: str) -> str:
    return _BROKER_TO_PAPER_STATUS.get(broker_status, OrderStatus.PENDING.value)


class LiveExecutionService:
    """Execute orders through a broker adapter, mirroring fills into the ledger."""

    def __init__(self, db: Session, broker: BrokerAdapter) -> None:
        self.db = db
        self.broker = broker
        self.orders = OrderRepository(db)
        self.positions = PositionRepository(db)
        self.trades = TradeRepository(db)
        self.instruments = InstrumentRepository(db)

    # ------------------------------------------------------------------ #
    # Guards
    # ------------------------------------------------------------------ #
    @staticmethod
    def _assert_enabled() -> None:
        if not settings.LIVE_EXECUTION_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Live execution is disabled on this deployment.",
            )

    def _get_portfolio(self, user_id: UUID, portfolio_id: UUID) -> Portfolio:
        portfolio = self.db.get(Portfolio, portfolio_id)
        if portfolio is None or portfolio.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found.",
            )
        if portfolio.execution_mode != ExecutionMode.LIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portfolio is not in live execution mode.",
            )
        return portfolio

    def _get_order(
        self, user_id: UUID, portfolio_id: UUID, order_id: UUID
    ) -> Order:
        order = self.orders.get_for_portfolio(portfolio_id, order_id)
        if order is None or order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        if order.execution_mode != ExecutionMode.LIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not a live order.",
            )
        return order

    def _get_active_instrument(self, instrument_id: UUID) -> Instrument:
        instrument = self.instruments.get(instrument_id)
        if instrument is None or not instrument.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found.",
            )
        return instrument

    # ------------------------------------------------------------------ #
    # Order lifecycle
    # ------------------------------------------------------------------ #
    async def place_order(
        self, user_id: UUID, portfolio_id: UUID, data: OrderCreate
    ) -> Order:
        self._assert_enabled()
        portfolio = self._get_portfolio(user_id, portfolio_id)
        if portfolio.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portfolio is not active.",
            )
        instrument = self._get_active_instrument(data.instrument_id)

        request = BrokerOrderRequest(
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            side=data.side,
            order_type=data.order_type,
            quantity=data.quantity,
            limit_price=data.limit_price,
        )
        result = await self.broker.place_order(request)

        order = Order(
            user_id=user_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument.id,
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            side=data.side.value,
            order_type=data.order_type.value,
            quantity=data.quantity,
            limit_price=data.limit_price,
            execution_mode=ExecutionMode.LIVE.value,
            broker_order_id=result.broker_order_id,
            status=_map_broker_status(result.status),
        )
        self.db.add(order)
        self.db.flush()

        if result.status in ("filled", "partially_filled") and result.filled_quantity:
            price = result.avg_fill_price or data.limit_price
            if price is None:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Broker reported a fill without an average price.",
                )
            self._book_fill(
                order,
                portfolio,
                quantity=result.filled_quantity,
                price=price,
            )
            order.status = (
                OrderStatus.FILLED.value
                if result.filled_quantity >= order.quantity
                else OrderStatus.PARTIALLY_FILLED.value
            )

        self.db.commit()
        self.db.refresh(order)
        return order

    async def cancel_order(
        self, user_id: UUID, portfolio_id: UUID, order_id: UUID
    ) -> Order:
        self._assert_enabled()
        order = self._get_order(user_id, portfolio_id, order_id)
        if order.status != OrderStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only pending orders can be cancelled (current status: {order.status}).",
            )
        if not order.broker_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no broker reference; cannot cancel.",
            )
        try:
            result = await self.broker.cancel_order(order.broker_order_id)
        except Exception as exc:  # pragma: no cover - network/upstream failures
            logger.exception("live cancel failed for %s", order.broker_order_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Broker cancel failed: {exc}",
            ) from exc
        order.status = _map_broker_status(result.status)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    async def refresh_order_status(
        self, user_id: UUID, portfolio_id: UUID, order_id: UUID
    ) -> Order:
        """Poll the broker and sync the order + ledger with the latest state."""
        self._assert_enabled()
        order = self._get_order(user_id, portfolio_id, order_id)
        if not order.broker_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no broker reference; cannot refresh.",
            )
        result = await self.broker.get_order_status(order.broker_order_id)
        order.status = _map_broker_status(result.status)
        if (
            result.status in ("filled", "partially_filled")
            and result.filled_quantity
            and order.filled_quantity in (None, 0)
        ):
            portfolio = self._get_portfolio(user_id, portfolio_id)
            price = result.avg_fill_price or order.limit_price
            if price is not None:
                self._book_fill(
                    order, portfolio, quantity=result.filled_quantity, price=price
                )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def _book_fill(
        self, order: Order, portfolio: Portfolio, *, quantity: int, price: Decimal
    ) -> None:
        """Mirror one broker-reported fill into the paper ledger."""
        price = _round_price(price)
        if order.side == OrderSide.BUY.value:
            portfolio.cash = _round_price(
                portfolio.cash - Decimal(quantity) * price
            )
        else:
            portfolio.cash = _round_price(
                portfolio.cash + Decimal(quantity) * price
            )

        instrument = self._get_active_instrument(order.instrument_id)
        position = self.positions.get_for_portfolio_instrument(
            portfolio.id, order.instrument_id
        )
        position, realized = _apply_fill(
            position,
            user_id=order.user_id,
            portfolio_id=portfolio.id,
            instrument=instrument,
            side=order.side,
            quantity=quantity,
            price=price,
        )
        self.db.add(position)
        self.db.add(
            Trade(
                user_id=order.user_id,
                portfolio_id=portfolio.id,
                order_id=order.id,
                instrument_id=order.instrument_id,
                symbol=order.symbol,
                exchange=order.exchange,
                side=order.side,
                quantity=quantity,
                price=price,
                realized_pnl=realized,
                executed_at=utcnow(),
            )
        )
        order.filled_quantity = quantity
        order.avg_fill_price = price
        order.filled_at = utcnow()
        self.db.add(order)
        self.db.add(portfolio)
