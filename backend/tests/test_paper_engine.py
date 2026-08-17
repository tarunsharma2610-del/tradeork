from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.domain.enums import OrderSide, OrderStatus, OrderType
from app.repositories.users import UserRepository
from app.schemas.order import OrderCreate
from app.schemas.portfolio import PortfolioCreate
from app.services.market_data import QuoteData
from app.services.paper_engine import PaperOrderEngine
from app.services.portfolios import PortfolioService


def make_quote(symbol: str, exchange: str, price: Decimal) -> QuoteData:
    return QuoteData(
        symbol=symbol,
        exchange=exchange,
        last_price=price,
        open=price,
        high=price,
        low=price,
        prev_close=price,
        volume=0,
        quote_time=datetime.now(UTC),
        is_mock=True,
        source="test",
    )


class FakeMarketData:
    def __init__(self, prices: dict[str, Decimal]) -> None:
        self.prices = prices

    def set(self, symbol: str, price: Decimal) -> None:
        self.prices[symbol] = price

    async def get_quotes(self, symbols, exchange: str) -> list[QuoteData]:
        return [
            make_quote(s, exchange, self.prices.get(s.upper(), Decimal("0")))
            for s in symbols
        ]


@pytest.fixture()
def trader(db_session, seeded_instruments):
    user = UserRepository(db_session).create(
        email="trader@example.com", password_hash=hash_password("x"), full_name=None
    )
    portfolio = PortfolioService(db_session).create(
        user.id,
        PortfolioCreate(
            name="Main", description=None, initial_capital=Decimal("100000")
        ),
    )
    engine = PaperOrderEngine(db_session, market_data=FakeMarketData({}))
    return {"user": user, "portfolio": portfolio, "engine": engine, "db": db_session}


def _instrument(db, symbol: str, exchange: str = "NSE"):
    from app.repositories.instruments import InstrumentRepository

    return InstrumentRepository(db).get_by_exchange_symbol(exchange, symbol)


def _buy(data: dict) -> OrderCreate:
    return OrderCreate(
        instrument_id=data["instrument_id"],
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=data["quantity"],
    )


def _order(
    inst_id, side: OrderSide, order_type: OrderType, quantity: int, limit=None
) -> OrderCreate:
    return OrderCreate(
        instrument_id=inst_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit,
    )


async def _place(trader, order: OrderCreate):
    return await trader["engine"].place_order(
        trader["user"].id, trader["portfolio"].id, order
    )


class TestPaperExecution:
    async def test_market_buy_opens_position(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader, _buy({"instrument_id": inst.id, "quantity": 10})
        )
        assert order.status == OrderStatus.FILLED.value
        assert order.filled_quantity == 10
        assert order.avg_fill_price == Decimal("100.00")
        pos = trader["engine"].positions.get_for_portfolio_instrument(
            trader["portfolio"].id, inst.id
        )
        assert pos is not None
        assert pos.quantity == 10
        assert pos.avg_price == Decimal("100.00")
        trader["db"].refresh(trader["portfolio"])
        assert trader["portfolio"].cash == Decimal("99000.00")

    async def test_market_sell_closes_position_with_pnl(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        md = trader["engine"].market_data
        md.set("RELIANCE", Decimal("100"))
        await _place(trader, _buy({"instrument_id": inst.id, "quantity": 10}))
        md.set("RELIANCE", Decimal("110"))
        sell = _order(inst.id, OrderSide.SELL, OrderType.MARKET, 10)
        await _place(trader, sell)
        pos = trader["engine"].positions.get_for_portfolio_instrument(
            trader["portfolio"].id, inst.id
        )
        assert pos.quantity == 0
        assert pos.realized_pnl == Decimal("100.00")
        trader["db"].refresh(trader["portfolio"])
        assert trader["portfolio"].cash == Decimal("100100.00")

    async def test_partial_close_accumulates_realized(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        md = trader["engine"].market_data
        md.set("RELIANCE", Decimal("100"))
        await _place(trader, _buy({"instrument_id": inst.id, "quantity": 10}))
        md.set("RELIANCE", Decimal("120"))
        await _place(trader, _order(inst.id, OrderSide.SELL, OrderType.MARKET, 4))
        pos = trader["engine"].positions.get_for_portfolio_instrument(
            trader["portfolio"].id, inst.id
        )
        assert pos.quantity == 6
        assert pos.avg_price == Decimal("100.00")
        assert pos.realized_pnl == Decimal("80.00")
        md.set("RELIANCE", Decimal("90"))
        await _place(trader, _order(inst.id, OrderSide.SELL, OrderType.MARKET, 6))
        trader["db"].refresh(pos)
        assert pos.quantity == 0
        assert pos.realized_pnl == Decimal("20.00")

    async def test_short_selling(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        md = trader["engine"].market_data
        md.set("RELIANCE", Decimal("100"))
        await _place(trader, _order(inst.id, OrderSide.SELL, OrderType.MARKET, 5))
        pos = trader["engine"].positions.get_for_portfolio_instrument(
            trader["portfolio"].id, inst.id
        )
        assert pos.quantity == -5
        assert pos.avg_price == Decimal("100.00")
        md.set("RELIANCE", Decimal("90"))
        await _place(trader, _order(inst.id, OrderSide.BUY, OrderType.MARKET, 2))
        trader["db"].refresh(pos)
        assert pos.quantity == -3
        assert pos.realized_pnl == Decimal("20.00")

    async def test_limit_buy_marketable_fills_at_limit(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader,
            _order(inst.id, OrderSide.BUY, OrderType.LIMIT, 10, limit=Decimal("105")),
        )
        assert order.status == OrderStatus.FILLED.value
        assert order.avg_fill_price == Decimal("105.00")

    async def test_limit_buy_not_marketable_stays_pending(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader,
            _order(inst.id, OrderSide.BUY, OrderType.LIMIT, 10, limit=Decimal("95")),
        )
        assert order.status == OrderStatus.PENDING.value
        assert trader["engine"].positions.get_for_portfolio_instrument(
            trader["portfolio"].id, inst.id
        ) is None

    async def test_limit_sell_above_market_stays_pending(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader,
            _order(inst.id, OrderSide.SELL, OrderType.LIMIT, 10, limit=Decimal("105")),
        )
        assert order.status == OrderStatus.PENDING.value

    async def test_insufficient_cash_rejects(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader, _buy({"instrument_id": inst.id, "quantity": 5000})
        )
        assert order.status == OrderStatus.REJECTED.value
        assert "Insufficient cash" in order.reject_reason

    async def test_cancel_pending_order(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader,
            _order(inst.id, OrderSide.BUY, OrderType.LIMIT, 10, limit=Decimal("95")),
        )
        cancelled = trader["engine"].cancel_order(
            trader["user"].id, trader["portfolio"].id, order.id
        )
        assert cancelled.status == OrderStatus.CANCELLED.value

    async def test_cancel_filled_order_conflicts(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        trader["engine"].market_data.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader, _buy({"instrument_id": inst.id, "quantity": 1})
        )
        with pytest.raises(HTTPException) as exc:
            trader["engine"].cancel_order(
                trader["user"].id, trader["portfolio"].id, order.id
            )
        assert exc.value.status_code == 409

    async def test_match_pending_fills_when_marketable(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        md = trader["engine"].market_data
        md.set("RELIANCE", Decimal("100"))
        order = await _place(
            trader,
            _order(inst.id, OrderSide.BUY, OrderType.LIMIT, 10, limit=Decimal("95")),
        )
        assert order.status == OrderStatus.PENDING.value
        md.set("RELIANCE", Decimal("90"))
        filled = await trader["engine"].match_pending_orders()
        assert filled == 1
        trader["db"].refresh(order)
        assert order.status == OrderStatus.FILLED.value
        assert order.avg_fill_price == Decimal("95.00")

    async def test_unknown_instrument_rejected(self, trader):
        import uuid

        with pytest.raises(HTTPException) as exc:
            await _place(
                trader, _buy({"instrument_id": uuid.uuid4(), "quantity": 1})
            )
        assert exc.value.status_code == 404

    async def test_summary_reflects_position_and_cash(self, trader):
        inst = _instrument(trader["db"], "RELIANCE")
        md = trader["engine"].market_data
        md.set("RELIANCE", Decimal("100"))
        await _place(trader, _buy({"instrument_id": inst.id, "quantity": 10}))
        summary = await trader["engine"].portfolio_summary(
            trader["user"].id, trader["portfolio"].id
        )
        assert summary["cash"] == Decimal("99000.00")
        assert summary["realized_pnl"] == Decimal("0.00")
        assert summary["unrealized_pnl"] == Decimal("0.00")
        assert summary["equity"] == Decimal("100000.00")
        assert summary["positions_count"] == 1
        md.set("RELIANCE", Decimal("110"))
        summary = await trader["engine"].portfolio_summary(
            trader["user"].id, trader["portfolio"].id
        )
        assert summary["unrealized_pnl"] == Decimal("100.00")
        assert summary["equity"] == Decimal("100100.00")
