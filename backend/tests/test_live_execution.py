from decimal import Decimal

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.domain.enums import ExecutionMode, OrderSide, OrderStatus, OrderType
from app.repositories.users import UserRepository
from app.schemas.order import OrderCreate
from app.schemas.portfolio import PortfolioCreate
from app.services.broker import (
    BrokerAdapter,
    BrokerOrderRequest,
    BrokerOrderResult,
)
from app.services.live_execution import LiveExecutionService
from app.services.paper_engine import PaperOrderEngine
from app.services.portfolios import PortfolioService
from tests.helpers import auth_headers, register_user
from tests.test_paper_engine import _instrument

PORTFOLIOS_URL = "/api/v1/portfolios"


def _make_portfolio(db, user_id, mode: ExecutionMode = ExecutionMode.LIVE):
    return PortfolioService(db).create(
        user_id,
        PortfolioCreate(
            name="Live",
            description=None,
            initial_capital=Decimal("100000"),
            execution_mode=mode,
        ),
    )


def _order(inst_id, side=OrderSide.BUY, order_type=OrderType.MARKET, qty=5, limit=None):
    return OrderCreate(
        instrument_id=inst_id,
        side=side,
        order_type=order_type,
        quantity=qty,
        limit_price=limit,
    )


class FakeLiveBroker(BrokerAdapter):
    """A non-mock broker simulator for API-level tests (is_mock=False).

    MARKET orders fill immediately; LIMIT orders rest as ``pending`` until
    ``fill()`` is called to simulate the broker crossing them later.
    """

    name = "fake-live"
    is_mock = False

    def __init__(self) -> None:
        self.orders: dict[str, dict] = {}
        self.placed: list[BrokerOrderRequest] = []
        self.cancelled: list[str] = []
        self._seq = 0

    async def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult:
        self._seq += 1
        broker_order_id = f"live-{self._seq}"
        self.placed.append(request)
        if request.order_type == OrderType.MARKET:
            status, filled, avg = "filled", request.quantity, Decimal("100.00")
        else:
            status, filled, avg = "pending", None, None
        self.orders[broker_order_id] = {
            "status": status,
            "filled_quantity": filled,
            "avg_fill_price": avg,
            "request": request,
        }
        return BrokerOrderResult(
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=filled,
            avg_fill_price=avg,
            raw={},
        )

    async def cancel_order(self, broker_order_id: str) -> BrokerOrderResult:
        self.cancelled.append(broker_order_id)
        if self.orders.get(broker_order_id, {}).get("status") != "pending":
            return BrokerOrderResult(broker_order_id=broker_order_id, status="rejected")
        self.orders[broker_order_id] = {
            "status": "cancelled",
            "filled_quantity": None,
            "avg_fill_price": None,
            "request": self.orders[broker_order_id]["request"],
        }
        return BrokerOrderResult(broker_order_id=broker_order_id, status="cancelled")

    def fill(self, broker_order_id: str) -> None:
        entry = self.orders[broker_order_id]
        request = entry["request"]
        entry["status"] = "filled"
        entry["filled_quantity"] = request.quantity
        entry["avg_fill_price"] = Decimal("95.00")

    async def get_order_status(self, broker_order_id: str) -> BrokerOrderResult:
        entry = self.orders[broker_order_id]
        return BrokerOrderResult(
            broker_order_id=broker_order_id,
            status=entry["status"],
            filled_quantity=entry["filled_quantity"],
            avg_fill_price=entry["avg_fill_price"],
            raw={},
        )


@pytest.fixture()
def live_enabled(monkeypatch):
    monkeypatch.setattr(settings, "LIVE_EXECUTION_ENABLED", True)
    return monkeypatch


@pytest.fixture()
def live_trader(db_session, seeded_instruments, live_enabled):
    user = UserRepository(db_session).create(
        email="live@example.com", password_hash=hash_password("x"), full_name=None
    )
    portfolio = _make_portfolio(db_session, user.id)
    service = LiveExecutionService(db_session, FakeLiveBroker())
    return {"user": user, "portfolio": portfolio, "service": service, "db": db_session}


class TestLiveExecutionService:
    async def test_place_market_order_fills_and_books_ledger(self, live_trader):
        inst = _instrument(live_trader["db"], "RELIANCE")
        order = await live_trader["service"].place_order(
            live_trader["user"].id, live_trader["portfolio"].id,
            _order(inst.id),
        )
        assert order.execution_mode == ExecutionMode.LIVE.value
        assert order.status == OrderStatus.FILLED.value
        assert order.broker_order_id is not None
        assert order.filled_quantity == 5
        pos = live_trader["service"].positions.get_for_portfolio_instrument(
            live_trader["portfolio"].id, inst.id
        )
        assert pos is not None
        assert pos.quantity == 5
        live_trader["db"].refresh(live_trader["portfolio"])
        assert live_trader["portfolio"].cash == Decimal("99500.00")

    async def test_place_limit_order_stays_pending(self, live_trader):
        inst = _instrument(live_trader["db"], "RELIANCE")
        order = await live_trader["service"].place_order(
            live_trader["user"].id, live_trader["portfolio"].id,
            _order(inst.id, order_type=OrderType.LIMIT, limit=Decimal("95")),
        )
        assert order.status == OrderStatus.PENDING.value
        assert order.broker_order_id is not None

    async def test_cancel_pending_live_order(self, live_trader):
        inst = _instrument(live_trader["db"], "RELIANCE")
        order = await live_trader["service"].place_order(
            live_trader["user"].id, live_trader["portfolio"].id,
            _order(inst.id, order_type=OrderType.LIMIT, limit=Decimal("95")),
        )
        cancelled = await live_trader["service"].cancel_order(
            live_trader["user"].id, live_trader["portfolio"].id, order.id
        )
        assert cancelled.status == OrderStatus.CANCELLED.value
        assert live_trader["service"].broker.cancelled == [order.broker_order_id]

    async def test_refresh_syncs_status(self, live_trader):
        inst = _instrument(live_trader["db"], "RELIANCE")
        order = await live_trader["service"].place_order(
            live_trader["user"].id, live_trader["portfolio"].id,
            _order(inst.id, order_type=OrderType.LIMIT, limit=Decimal("95")),
        )
        assert order.status == OrderStatus.PENDING.value
        live_trader["service"].broker.fill(order.broker_order_id)
        refreshed = await live_trader["service"].refresh_order_status(
            live_trader["user"].id, live_trader["portfolio"].id, order.id
        )
        assert refreshed.status == OrderStatus.FILLED.value

    async def test_paper_portfolio_rejected(self, db_session, seeded_instruments):
        user = UserRepository(db_session).create(
            email="paper-live@example.com",
            password_hash=hash_password("x"),
            full_name=None,
        )
        portfolio = _make_portfolio(db_session, user.id, mode=ExecutionMode.PAPER)
        service = LiveExecutionService(db_session, FakeLiveBroker())
        with pytest.raises(Exception) as exc:
            await service.place_order(
                user.id, portfolio.id, _order(_instrument(db_session, "RELIANCE").id)
            )
        assert exc.value.status_code == 400

    async def test_disabled_raises(self, db_session, seeded_instruments):
        user = UserRepository(db_session).create(
            email="disabled@example.com",
            password_hash=hash_password("x"),
            full_name=None,
        )
        portfolio = PortfolioService(db_session).create(
            user.id,
            PortfolioCreate(
                name="Live",
                description=None,
                initial_capital=Decimal("100000"),
                execution_mode=ExecutionMode.PAPER,
            ),
        )
        portfolio.execution_mode = ExecutionMode.LIVE.value
        db_session.add(portfolio)
        db_session.commit()
        service = LiveExecutionService(db_session, FakeLiveBroker())
        with pytest.raises(Exception) as exc:
            await service.place_order(
                user.id, portfolio.id, _order(_instrument(db_session, "RELIANCE").id)
            )
        assert exc.value.status_code == 400

    async def test_ownership_enforced(self, live_trader):
        user_b = UserRepository(live_trader["db"]).create(
            email="other-live@example.com",
            password_hash=hash_password("x"),
            full_name=None,
        )
        with pytest.raises(Exception) as exc:
            await live_trader["service"].place_order(
                user_b.id,
                live_trader["portfolio"].id,
                _order(_instrument(live_trader["db"], "RELIANCE").id),
            )
        assert exc.value.status_code == 404

    async def test_paper_matcher_skips_live_orders(self, live_trader):
        inst = _instrument(live_trader["db"], "RELIANCE")
        await live_trader["service"].place_order(
            live_trader["user"].id, live_trader["portfolio"].id,
            _order(inst.id, order_type=OrderType.LIMIT, limit=Decimal("95")),
        )
        paper_engine = PaperOrderEngine(live_trader["db"])
        filled = await paper_engine.match_pending_orders()
        assert filled == 0


class TestLiveExecutionApi:
    def test_create_live_portfolio_requires_enabled(
        self, client, seeded_instruments, live_enabled
    ):
        headers = auth_headers(register_user(client, "liveapi@example.com"))
        res = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        )
        assert res.status_code == 201, res.text
        assert res.json()["execution_mode"] == "live"

    def test_create_live_portfolio_disabled_rejected(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "liveapi2@example.com"))
        res = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        )
        assert res.status_code == 400, res.text

    def test_live_order_requires_live_broker(self, client, seeded_instruments, live_enabled):
        headers = auth_headers(register_user(client, "liveapi3@example.com"))
        portfolio = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        ).json()
        inst = client.get(
            "/api/v1/instruments",
            params={"q": "RELIANCE", "exchange": "NSE", "instrument_type": "EQUITY"},
        ).json()[0]
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 5,
            },
        )
        assert res.status_code == 400, res.text

    def test_live_order_flow(self, client, seeded_instruments, live_enabled, monkeypatch):
        import app.api.v1.endpoints.trading as trading_module

        broker = FakeLiveBroker()
        monkeypatch.setattr(trading_module, "get_broker", lambda: broker)
        headers = auth_headers(register_user(client, "liveapi4@example.com"))
        portfolio = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        ).json()
        inst = client.get(
            "/api/v1/instruments",
            params={"q": "RELIANCE", "exchange": "NSE", "instrument_type": "EQUITY"},
        ).json()[0]

        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 5,
            },
        )
        assert res.status_code == 201, res.text
        order = res.json()
        assert order["execution_mode"] == "live"
        assert order["status"] == "filled"
        assert order["broker_order_id"] is not None

        summary = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/summary", headers=headers
        ).json()
        assert summary["positions_count"] == 1

        pos = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/positions", headers=headers
        ).json()
        assert pos[0]["quantity"] == 5

    def test_refresh_on_paper_portfolio_rejected(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "liveapi5@example.com"))
        portfolio = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={"name": "Paper", "initial_capital": "100000.00"},
        ).json()
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders"
            "/00000000-0000-0000-0000-000000000000/refresh",
            headers=headers,
        )
        assert res.status_code == 400, res.text
