from decimal import Decimal

import httpx
import pytest

from app.services.upstox import UpstoxAPIError, UpstoxMarketDataProvider


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = "" if status_code < 400 else "boom"

    def json(self):
        return self._payload


async def _run_provider(fake_get, symbols, exchange, **kwargs):
    provider = UpstoxMarketDataProvider(
        api_key="test-key", access_token="test-token", **kwargs
    )
    return await provider.get_quotes(symbols, exchange)


class TestUpstoxProvider:
    async def test_parses_success_payload(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            assert params == {"symbol": "NSE:RELIANCE"}
            return FakeResponse(
                200,
                {
                    "status": "success",
                    "data": {
                        "NSE:RELIANCE": {
                            "trading_symbol": "RELIANCE",
                            "exchange": "NSE",
                            "last_price": 2984.5,
                            "volume": 12345,
                            "ohlc": {
                                "open": 2980.0,
                                "high": 2995.0,
                                "low": 2975.0,
                                "close": 2981.0,
                            },
                            "timestamp": "2024-06-01T10:30:00+05:30",
                        }
                    },
                },
            )

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        quotes = await _run_provider(fake_get, ["RELIANCE"], "NSE")
        assert len(quotes) == 1
        q = quotes[0]
        assert q.symbol == "RELIANCE"
        assert q.exchange == "NSE"
        assert q.last_price == Decimal("2984.5")
        assert q.open == Decimal("2980.0")
        assert q.high == Decimal("2995.0")
        assert q.low == Decimal("2975.0")
        assert q.prev_close == Decimal("2981.0")
        assert q.volume == 12345
        assert q.is_mock is False
        assert q.source == "upstox"

    async def test_omits_unknown_symbols(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            return FakeResponse(
                200,
                {
                    "status": "success",
                    "data": {"MCX:GOLD": {"trading_symbol": "GOLD", "exchange": "MCX"}},
                },
            )

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        quotes = await _run_provider(fake_get, ["GOLD", "ZZZZ"], "MCX")
        assert [q.symbol for q in quotes] == ["GOLD"]

    async def test_http_error_raises(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            return FakeResponse(500, {})

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        with pytest.raises(UpstoxAPIError):
            await _run_provider(fake_get, ["RELIANCE"], "NSE")

    async def test_api_error_status_raises(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            return FakeResponse(200, {"status": "error", "errors": [{"message": "nope"}]})

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        with pytest.raises(UpstoxAPIError):
            await _run_provider(fake_get, ["RELIANCE"], "NSE")

    async def test_transport_error_raises(self, monkeypatch):
        async def fake_get(self, url, params=None, headers=None):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
        with pytest.raises(UpstoxAPIError):
            await _run_provider(fake_get, ["RELIANCE"], "NSE")
