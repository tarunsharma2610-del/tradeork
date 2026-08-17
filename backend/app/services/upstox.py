"""Upstox v2 REST market-data provider (live).

This is a real-market provider: `is_mock = False` and `source = "upstox"`.
Quotes are fetched from the Upstox v2 `market-quote/quotes` endpoint. The
access token is supplied through configuration; an OAuth refresh flow is
intentionally out of scope for now.
"""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.services.market_data import QuoteData

logger = logging.getLogger(__name__)


class UpstoxAPIError(Exception):
    """Raised when the Upstox API cannot be reached or returns an error."""


class UpstoxMarketDataProvider:
    """Live quotes from Upstox v2 `GET /market-quote/quotes`.

    Symbols are sent in the `EXCHANGE:SECURITY` form the API expects (e.g.
    ``NSE:RELIANCE``, ``MCX:GOLD``). Symbols the API does not recognise are
    silently omitted from the returned quotes so the caller can surface a
    friendly per-symbol error.
    """

    name = "upstox"
    is_mock = False

    def __init__(
        self,
        *,
        api_key: str,
        access_token: str,
        base_url: str = "https://api.upstox.com/v2",
        timeout: float = 5.0,
    ) -> None:
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    async def get_quotes(
        self, symbols: Sequence[str], exchange: str
    ) -> list[QuoteData]:
        keys = [f"{exchange}:{symbol}" for symbol in symbols]
        if not keys:
            return []
        params = {"symbol": ",".join(keys)}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/market-quote/quotes",
                    params=params,
                    headers=self._headers(),
                )
        except httpx.HTTPError as exc:
            raise UpstoxAPIError(f"Upstox request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise UpstoxAPIError(
                f"Upstox returned HTTP {resp.status_code}: {resp.text[:200]}"
            )
        body = resp.json()
        if body.get("status") != "success":
            raise UpstoxAPIError(f"Upstox error: {body.get('errors') or body}")
        data = body.get("data") or {}
        return [
            self._parse_quote(key, data[key])
            for key in keys
            if data.get(key)
        ]

    def _parse_quote(self, key: str, item: dict[str, Any]) -> QuoteData:
        symbol = item.get("trading_symbol") or key.split(":")[-1]
        exchange = (item.get("exchange") or key.split(":")[0]).upper()
        ohlc = item.get("ohlc") or {}
        raw_ts = item.get("timestamp")
        if raw_ts:
            try:
                quote_time = datetime.fromisoformat(
                    str(raw_ts).replace("Z", "+00:00")
                )
            except ValueError:
                quote_time = datetime.now(UTC)
        else:
            quote_time = datetime.now(UTC)
        return QuoteData(
            symbol=symbol,
            exchange=exchange,
            last_price=Decimal(str(item.get("last_price") or 0)),
            open=Decimal(str(ohlc.get("open") or 0)),
            high=Decimal(str(ohlc.get("high") or 0)),
            low=Decimal(str(ohlc.get("low") or 0)),
            prev_close=Decimal(str(ohlc.get("close") or 0)),
            volume=int(item.get("volume") or 0),
            quote_time=quote_time,
            is_mock=False,
            source=self.name,
        )
