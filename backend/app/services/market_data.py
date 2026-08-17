import hashlib
import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from app.core.redis import get_redis_client


@dataclass(frozen=True)
class QuoteData:
    """Canonical quote value object shared by every market data source."""

    symbol: str
    exchange: str
    last_price: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    prev_close: Decimal
    volume: int
    quote_time: datetime
    is_mock: bool
    source: str


class MarketDataProvider(Protocol):
    """Abstraction over any market data source.

    Real implementations (broker feeds, exchange vendors) must set
    `is_mock = False` and identify themselves via `name`.
    """

    name: str
    is_mock: bool

    async def get_quotes(
        self, symbols: Sequence[str], exchange: str
    ) -> list[QuoteData]: ...


def _round_price(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


class MockMarketDataProvider:
    """Synthetic quote generator for development and paper trading only.

    This is **mock data** and is always labelled as such via `is_mock=True`
    and `source="mock"` so it can never be mistaken for real market data.
    """

    name = "mock"
    is_mock = True

    async def get_quotes(
        self, symbols: Sequence[str], exchange: str
    ) -> list[QuoteData]:
        return [self._quote(symbol, exchange) for symbol in symbols]

    def _quote(self, symbol: str, exchange: str) -> QuoteData:
        prev_close = self._base_price(symbol)
        bucket = int(time.time() // 15)
        seed = int(
            hashlib.sha256(f"{exchange}:{symbol}:{bucket}".encode()).hexdigest()[:8],
            16,
        )
        drift = Decimal(seed % 401 - 200) / Decimal(10000)  # -2% .. +2%
        last = _round_price(prev_close * (1 + drift))
        spread = Decimal(seed % 50) / Decimal(1000)
        high = _round_price(max(last, prev_close) * (1 + spread))
        low = _round_price(min(last, prev_close) * (1 - spread))
        open_ = _round_price(
            prev_close * (1 + Decimal((seed >> 8) % 201 - 100) / Decimal(10000))
        )
        volume = 1000 + seed % 49000
        return QuoteData(
            symbol=symbol,
            exchange=exchange,
            last_price=last,
            open=open_,
            high=high,
            low=low,
            prev_close=prev_close,
            volume=volume,
            quote_time=datetime.now(UTC),
            is_mock=True,
            source=self.name,
        )

    def _base_price(self, symbol: str) -> Decimal:
        seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)
        # Stable per-symbol base price between 10.00 and ~911.00
        return _round_price(Decimal(seed % 90000 + 1000) / Decimal(100))


def _quote_to_json(q: QuoteData) -> dict:
    return {
        "symbol": q.symbol,
        "exchange": q.exchange,
        "last_price": str(q.last_price),
        "open": str(q.open),
        "high": str(q.high),
        "low": str(q.low),
        "prev_close": str(q.prev_close),
        "volume": q.volume,
        "quote_time": q.quote_time.isoformat(),
        "is_mock": q.is_mock,
        "source": q.source,
    }


def _quote_from_json(data: dict) -> QuoteData:
    return QuoteData(
        symbol=data["symbol"],
        exchange=data["exchange"],
        last_price=Decimal(data["last_price"]),
        open=Decimal(data["open"]),
        high=Decimal(data["high"]),
        low=Decimal(data["low"]),
        prev_close=Decimal(data["prev_close"]),
        volume=int(data["volume"]),
        quote_time=datetime.fromisoformat(data["quote_time"]),
        is_mock=bool(data["is_mock"]),
        source=data["source"],
    )


class MarketDataService:
    """Orchestrates market data delivery with a short-lived Redis cache.

    The cache degrades gracefully: if Redis is unreachable the provider is
    called directly, so market data availability never depends on the cache.
    """

    def __init__(self, provider: MarketDataProvider, cache_ttl: int = 2) -> None:
        self.provider = provider
        self.cache_ttl = cache_ttl

    async def get_quotes(
        self, symbols: Sequence[str], exchange: str
    ) -> list[QuoteData]:
        quotes: dict[str, QuoteData] = {}
        missing: list[str] = []
        for symbol in symbols:
            cached = await self._cache_get(exchange, symbol)
            if cached is not None:
                quotes[symbol] = cached
            else:
                missing.append(symbol)
        if missing:
            fetched = await self.provider.get_quotes(missing, exchange)
            for quote in fetched:
                quotes[quote.symbol] = quote
                await self._cache_set(exchange, quote.symbol, quote)
        return [quotes[s] for s in symbols if s in quotes]

    async def _cache_get(self, exchange: str, symbol: str) -> QuoteData | None:
        try:
            client = get_redis_client()
            raw = await client.get(f"quote:{exchange}:{symbol}")
        except Exception:
            return None
        if not raw:
            return None
        try:
            return _quote_from_json(json.loads(raw))
        except (ValueError, KeyError, TypeError):
            return None

    async def _cache_set(
        self, exchange: str, symbol: str, quote: QuoteData
    ) -> None:
        try:
            client = get_redis_client()
            await client.set(
                f"quote:{exchange}:{symbol}",
                json.dumps(_quote_to_json(quote)),
                ex=self.cache_ttl,
            )
        except Exception:
            pass


mock_market_data_service = MarketDataService(MockMarketDataProvider())
