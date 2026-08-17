from decimal import Decimal

import httpx
import pytest

from app.core.config import settings
from app.domain.enums import OrderSide, OrderType
from app.services.broker import (
    BrokerAdapter,
    BrokerAPIError,
    BrokerOrderRequest,
    MockBrokerAdapter,
)
from app.services.broker_factory import get_broker
from app.services.upstox_broker import UpstoxBrokerAdapter


def _request(
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=5,
    limit=None,
) -> BrokerOrderRequest:
    return BrokerOrderRequest(
        symbol="RELIANCE",
        exchange="NSE",
        side=side,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit,
    )


class TestMockBrokerAdapter:
    async def test_market_order_fills_immediately(self):
        adapter = MockBrokerAdapter()
        result = await adapter.place_order(_request())
        assert result.status == "filled"
        assert result.filled_quantity == 5
        assert result.broker_order_id.startswith("mock-")

    async def test_limit_order_rests_pending(self):
        adapter = MockBrokerAdapter()
        result = await adapter.place_order(
            _request(order_type=OrderType.LIMIT, limit=Decimal("100"))
        )
        assert result.status == "pending"
        assert result.filled_quantity is None

    async def test_cancel_pending_order(self):
        adapter = MockBrokerAdapter()
        order = await adapter.place_order(
            _request(order_type=OrderType.LIMIT, limit=Decimal("100"))
        )
        cancelled = await adapter.cancel_order(order.broker_order_id)
        assert cancelled.status == "cancelled"

    async def test_cancel_filled_order_raises(self):
        adapter = MockBrokerAdapter()
        order = await adapter.place_order(_request())
        with pytest.raises(BrokerAPIError):
            await adapter.cancel_order(order.broker_order_id)

    async def test_status_unknown_order_raises(self):
        adapter = MockBrokerAdapter()
        with pytest.raises(BrokerAPIError):
            await adapter.get_order_status("mock-missing")

    async def test_is_mock_true(self):
        assert MockBrokerAdapter().is_mock is True


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = "" if status_code < 400 else "boom"

    def json(self):
        return self._payload


class TestUpstoxBrokerAdapter:
    def _adapter(self, **kwargs) -> UpstoxBrokerAdapter:
        return UpstoxBrokerAdapter(
            api_key="test-key", access_token="test-token", **kwargs
        )

    async def test_place_order_sends_payload_and_parses_id(self, monkeypatch):
        captured = {}

        async def fake_post(self, url, json=None, headers=None, params=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse(200, {"status": "success", "data": {"order_id": "UP1"}})

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        result = await self._adapter().place_order(_request())
        assert result.broker_order_id == "UP1"
        assert result.status == "pending"
        assert captured["url"].endswith("/order/place")
        assert captured["json"]["instrument_token"] == "NSE:RELIANCE"
        assert captured["json"]["order_type"] == "MARKET"
        assert captured["json"]["quantity"] == 5
        assert captured["json"]["price"] == "0"

    async def test_place_limit_order_sends_price(self, monkeypatch):
        captured = {}

        async def fake_post(self, url, json=None, headers=None, params=None):
            captured["json"] = json
            return FakeResponse(200, {"status": "success", "data": {"order_id": "UP2"}})

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        await self._adapter().place_order(
            _request(order_type=OrderType.LIMIT, limit=Decimal("99.5"))
        )
        assert captured["json"]["price"] == "99.5"

    async def test_place_limit_without_price_raises(self, monkeypatch):
        async def fake_post(self, url, json=None, headers=None, params=None):
            raise AssertionError("should not hit the API")

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(BrokerAPIError):
            await self._adapter().place_order(
                _request(order_type=OrderType.LIMIT, limit=None)
            )

    async def test_cancel_order(self, monkeypatch):
        captured = {}

        async def fake_delete(self, url, json=None, headers=None, params=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse(
                200, {"status": "success", "data": {"order_id": "UP1"}}
            )

        monkeypatch.setattr(httpx.AsyncClient, "delete", fake_delete)
        result = await self._adapter().cancel_order("UP1")
        assert result.status == "cancelled"
        assert captured["url"].endswith("/order/cancel")
        assert captured["json"]["order_id"] == "UP1"

    async def test_get_order_status_maps_fields(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            return FakeResponse(
                200,
                {
                    "status": "success",
                    "data": {
                        "order_id": "UP1",
                        "status": "complete",
                        "filled_quantity": 5,
                        "average_price": 100.5,
                    },
                },
            )

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        result = await self._adapter().get_order_status("UP1")
        assert result.status == "filled"
        assert result.filled_quantity == 5
        assert result.avg_fill_price == Decimal("100.5")

    async def test_http_error_raises(self, monkeypatch):
        async def fake_post(self, url, json=None, headers=None, params=None):
            return FakeResponse(500, {})

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(BrokerAPIError):
            await self._adapter().place_order(_request())

    async def test_api_error_status_raises(self, monkeypatch):
        async def fake_post(self, url, json=None, headers=None, params=None):
            return FakeResponse(
                200, {"status": "error", "errors": [{"message": "nope"}]}
            )

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(BrokerAPIError):
            await self._adapter().place_order(_request())

    async def test_transport_error_raises(self, monkeypatch):
        async def fake_post(self, url, json=None, headers=None, params=None):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(BrokerAPIError):
            await self._adapter().place_order(_request())

    async def test_is_mock_false(self):
        assert self._adapter().is_mock is False


@pytest.fixture()
def _reset_broker_settings(monkeypatch):
    monkeypatch.setattr(settings, "BROKER_ADAPTER", "mock")
    monkeypatch.setattr(settings, "UPSTOX_API_KEY", "")
    monkeypatch.setattr(settings, "UPSTOX_ACCESS_TOKEN", "")
    return monkeypatch


class TestBrokerFactory:
    async def test_default_is_mock(self, _reset_broker_settings):
        broker = get_broker()
        assert isinstance(broker, MockBrokerAdapter)
        assert broker.is_mock is True

    async def test_upstox_when_configured(self, _reset_broker_settings):
        settings.BROKER_ADAPTER = "upstox"
        settings.UPSTOX_API_KEY = "k"
        settings.UPSTOX_ACCESS_TOKEN = "t"
        broker = get_broker()
        assert isinstance(broker, UpstoxBrokerAdapter)
        assert broker.is_mock is False

    async def test_upstox_without_credentials_falls_back_to_mock(
        self, _reset_broker_settings
    ):
        settings.BROKER_ADAPTER = "upstox"
        settings.UPSTOX_API_KEY = ""
        settings.UPSTOX_ACCESS_TOKEN = ""
        broker = get_broker()
        assert isinstance(broker, MockBrokerAdapter)
        assert broker.is_mock is True

    async def test_returns_broker_adapter_interface(self, _reset_broker_settings):
        assert isinstance(get_broker(), BrokerAdapter)
