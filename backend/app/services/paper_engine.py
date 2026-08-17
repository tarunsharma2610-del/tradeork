"""Strictly-paper trading execution engine.

Every fill is simulated against the configured market-data provider (mock
or live) and booked in the paper ledger. **No order is ever sent to a
broker.** This is the PAPER side of the PAPER/LIVE separation: a future
live adapter can reuse the same order semantics through a different
execution seam, but nothing here can touch a real account.

Accounting model:
- Portfolio.cash starts at initial_capital; BUY fills debit it, SELL fills
  credit it.
- Positions are aggregated per (portfolio, instrument) with signed net
  quantity (positive = long, negative = short) and a volume-weighted
  average entry price. Realized P&L accrues when a fill reduces or closes
  an existing position.
- Equity = cash + sum(last_price * quantity) over open positions.
"""

import asyncio
import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import utcnow
from app.domain.enums import OrderStatus, OrderType
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.repositories.instruments import InstrumentRepository
from app.repositories.orders import OrderRepository
from app.repositories.positions import PositionRepository
from app.repositories.trades import TradeRepository
from app.schemas.order import OrderCreate
from app.services.market_data import MarketDataService, QuoteData
from app.services.provider_factory import get_provider

logger = logging.getLogger(__name__)

_PRICE = Decimal("0.01")


def _round_price(value: Decimal) -> Decimal:
    return value.quantize(_PRICE)


def _apply_fill(
    position: Position | None,
    *,
    user_id: UUID,
    portfolio_id: UUID,
    instrument: Instrument,
    side: str,
    quantity: int,
    price: Decimal,
) -> tuple[Position, Decimal]:
    """Update an aggregated position for one fill; returns (position, realized_pnl)."""
    qty = Decimal(quantity)
    realized = Decimal("0")
    if position is None:
        position = Position(
            user_id=user_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument.id,
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            quantity=quantity if side == "BUY" else -quantity,
            avg_price=price,
            realized_pnl=Decimal("0"),
        )
        return position, realized

    net = position.quantity
    avg = position.avg_price
    if side == "BUY":
        if net < 0:
            if quantity <= -net:
                realized = _round_price((avg - price) * qty)
                position.quantity = net + quantity
                if position.quantity == 0:
                    position.avg_price = Decimal("0")
            else:
                close = -net
                realized = _round_price((avg - price) * Decimal(close))
                position.quantity = quantity - close
                position.avg_price = price
        else:
            total = Decimal(net) + qty
            position.avg_price = _round_price(
                (Decimal(net) * avg + qty * price) / total
            )
            position.quantity = net + quantity
    else:  # SELL
        if net > 0:
            if quantity <= net:
                realized = _round_price((price - avg) * qty)
                position.quantity = net - quantity
                if position.quantity == 0:
                    position.avg_price = Decimal("0")
            else:
                close = net
                realized = _round_price((price - avg) * Decimal(close))
                position.quantity = net - quantity
                position.avg_price = price
        else:
            total = Decimal(-net) + qty
            position.avg_price = _round_price(
                (Decimal(-net) * avg + qty * price) / total
            )
            position.quantity = net - quantity

    position.realized_pnl = _round_price(position.realized_pnl + realized)
    return position, realized


class PaperOrderEngine:
    """Paper execution operations, always scoped to the owning user."""

    def __init__(self, db: Session, market_data: MarketDataService | None = None) -> None:
        self.db = db
        self.market_data = market_data or MarketDataService(get_provider())
        self.orders = OrderRepository(db)
        self.positions = PositionRepository(db)
        self.trades = TradeRepository(db)
        self.instruments = InstrumentRepository(db)

    # ------------------------------------------------------------------ #
    # Ownership helpers
    # ------------------------------------------------------------------ #
    def _get_portfolio(self, user_id: UUID, portfolio_id: UUID) -> Portfolio:
        portfolio = self.db.get(Portfolio, portfolio_id)
        if portfolio is None or portfolio.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found.",
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
    # Quote resolution
    # ------------------------------------------------------------------ #
    async def _resolve_quote(self, symbol: str, exchange: str) -> QuoteData | None:
        try:
            quotes = await self.market_data.get_quotes([symbol], exchange)
        except Exception:
            return None
        for quote in quotes:
            if quote.symbol.upper() == symbol.upper() and quote.last_price > 0:
                return quote
        return None

    # ------------------------------------------------------------------ #
    # Order lifecycle
    # ------------------------------------------------------------------ #
    async def place_order(
        self, user_id: UUID, portfolio_id: UUID, data: OrderCreate
    ) -> Order:
        portfolio = self._get_portfolio(user_id, portfolio_id)
        if portfolio.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portfolio is not active.",
            )
        instrument = self._get_active_instrument(data.instrument_id)

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
            status=OrderStatus.PENDING.value,
        )
        self.db.add(order)
        self.db.flush()

        await self._attempt_fill(order, portfolio)
        self.db.refresh(order)
        return order

    async def _attempt_fill(self, order: Order, portfolio: Portfolio) -> None:
        quote = await self._resolve_quote(order.symbol, order.exchange)
        if quote is None:
            self._reject(order, f"Market price unavailable for {order.symbol}.")
            self.db.commit()
            return

        last = quote.last_price
        if order.order_type == OrderType.MARKET.value:
            fill_price = last
        elif order.side == "BUY":
            if order.limit_price is None or order.limit_price < last:
                self.db.commit()
                return  # not marketable yet; stays pending for the matcher
            fill_price = order.limit_price
        else:  # SELL limit
            if order.limit_price is None or order.limit_price > last:
                self.db.commit()
                return  # not marketable yet; stays pending for the matcher
            fill_price = order.limit_price

        fill_price = _round_price(fill_price)
        cost = Decimal(order.quantity) * fill_price

        if order.side == "BUY" and cost > portfolio.cash:
            self._reject(
                order,
                f"Insufficient cash: need {cost:.2f}, available {portfolio.cash:.2f}.",
            )
            self.db.commit()
            return

        if order.side == "BUY":
            portfolio.cash = _round_price(portfolio.cash - cost)
        else:
            portfolio.cash = _round_price(portfolio.cash + cost)

        position = self.positions.get_for_portfolio_instrument(
            portfolio.id, order.instrument_id
        )
        position, realized = _apply_fill(
            position,
            user_id=order.user_id,
            portfolio_id=portfolio.id,
            instrument=self._get_active_instrument(order.instrument_id),
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
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
                quantity=order.quantity,
                price=fill_price,
                realized_pnl=realized,
                executed_at=utcnow(),
            )
        )
        order.status = OrderStatus.FILLED.value
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.filled_at = utcnow()
        self.db.add(order)
        self.db.add(portfolio)
        self.db.commit()

    def _reject(self, order: Order, reason: str) -> None:
        order.status = OrderStatus.REJECTED.value
        order.reject_reason = reason
        self.db.add(order)

    def cancel_order(self, user_id: UUID, portfolio_id: UUID, order_id: UUID) -> Order:
        order = self._get_order(user_id, portfolio_id, order_id)
        if order.status != OrderStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only pending orders can be cancelled (current status: {order.status}).",
            )
        order.status = OrderStatus.CANCELLED.value
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_orders(
        self, user_id: UUID, portfolio_id: UUID, status_filter: str | None = None
    ) -> list[Order]:
        self._get_portfolio(user_id, portfolio_id)
        return self.orders.list_for_portfolio(portfolio_id, status=status_filter)

    # ------------------------------------------------------------------ #
    # Positions + summary
    # ------------------------------------------------------------------ #
    async def list_positions(self, user_id: UUID, portfolio_id: UUID) -> list[dict]:
        self._get_portfolio(user_id, portfolio_id)
        positions = self.positions.list_for_portfolio(portfolio_id)
        marks = await self._mark_prices(positions)
        return [
            {
                **{
                    "id": p.id,
                    "portfolio_id": p.portfolio_id,
                    "instrument_id": p.instrument_id,
                    "symbol": p.symbol,
                    "exchange": p.exchange,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "realized_pnl": p.realized_pnl,
                    "updated_at": p.updated_at,
                },
                "last_price": marks.get(p.symbol, p.avg_price),
                "market_value": _round_price(
                    marks.get(p.symbol, p.avg_price) * Decimal(p.quantity)
                ),
                "unrealized_pnl": _round_price(
                    (marks.get(p.symbol, p.avg_price) - p.avg_price)
                    * Decimal(p.quantity)
                ),
            }
            for p in positions
        ]

    async def _mark_prices(self, positions: list[Position]) -> dict[str, Decimal]:
        by_exchange: dict[str, list[str]] = {}
        for p in positions:
            by_exchange.setdefault(p.exchange, []).append(p.symbol)
        marks: dict[str, Decimal] = {}
        for exchange, symbols in by_exchange.items():
            try:
                quotes = await self.market_data.get_quotes(symbols, exchange)
            except Exception:
                quotes = []
            for q in quotes:
                if q.last_price > 0:
                    marks[q.symbol.upper()] = q.last_price
        return marks

    async def portfolio_summary(self, user_id: UUID, portfolio_id: UUID) -> dict:
        portfolio = self._get_portfolio(user_id, portfolio_id)
        positions = self.positions.list_for_portfolio(portfolio_id)
        marks = await self._mark_prices(positions)

        realized = sum((p.realized_pnl for p in positions), Decimal("0"))
        unrealized = sum(
            (
                _round_price(
                    (marks.get(p.symbol, p.avg_price) - p.avg_price)
                    * Decimal(p.quantity)
                )
                for p in positions
            ),
            Decimal("0"),
        )
        open_value = sum(
            (
                _round_price(marks.get(p.symbol, p.avg_price) * Decimal(p.quantity))
                for p in positions
            ),
            Decimal("0"),
        )
        pending = len(self.orders.list_for_portfolio(portfolio_id, status="pending"))
        return {
            "portfolio_id": portfolio.id,
            "name": portfolio.name,
            "initial_capital": portfolio.initial_capital,
            "cash": portfolio.cash,
            "realized_pnl": _round_price(realized),
            "unrealized_pnl": _round_price(unrealized),
            "total_pnl": _round_price(realized + unrealized),
            "equity": _round_price(portfolio.cash + open_value),
            "positions_count": len(positions),
            "open_orders_count": pending,
        }

    # ------------------------------------------------------------------ #
    # Background limit-order matching
    # ------------------------------------------------------------------ #
    async def match_pending_orders(self) -> int:
        """Fill any pending orders that are now marketable. Returns count filled."""
        pending = self.orders.list_pending()
        filled = 0
        for order in pending:
            portfolio = self.db.get(Portfolio, order.portfolio_id)
            if portfolio is None or portfolio.status != "active":
                continue
            before = order.status
            await self._attempt_fill(order, portfolio)
            self.db.expire_all()
            if order.status != before and order.status == OrderStatus.FILLED.value:
                filled += 1
        return filled


async def run_paper_matcher() -> None:
    """Background loop matching pending paper limit orders against live quotes."""
    logger.info("paper order matcher started (interval=%ss)", settings.PAPER_MATCHER_INTERVAL)
    while True:
        await asyncio.sleep(settings.PAPER_MATCHER_INTERVAL)
        try:
            with SessionLocal() as db:
                await PaperOrderEngine(db).match_pending_orders()
        except asyncio.CancelledError:
            logger.info("paper order matcher stopped")
            raise
        except Exception:
            logger.exception("paper order matcher iteration failed")
