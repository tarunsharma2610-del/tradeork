"""WebSocket quote streaming for a single client.

A background task periodically fetches quotes for the client's current
subscription through the same MarketDataService (and provider) as the REST
endpoint, and pushes them as JSON messages. Redis-cached quotes make the
poll interval cheap even with many connected clients.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.services.market_data import MarketDataService, _quote_to_json

Validator = Callable[[list[str], str], Awaitable[list[str]]]


class QuoteStreamService:
    """Streams quotes to one WebSocket client.

    The client may subscribe via query parameters on connect
    (``symbols``, ``exchange``) and/or at any time via messages:
    ``{"action": "subscribe", "symbols": [...], "exchange": "NSE"}``.

    If a ``validate_symbols`` callable is provided it is consulted whenever
    the subscription changes; unknown symbols are reported to the client as an
    ``error`` frame (``{"type": "error", "code": "unknown_symbols", ...}``)
    instead of being silently dropped.
    """

    def __init__(
        self,
        data_service: MarketDataService,
        interval: float = 2.0,
        validate_symbols: Validator | None = None,
    ) -> None:
        self.data_service = data_service
        self.interval = interval
        self.validate_symbols = validate_symbols

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        state: dict[str, Any] = {
            "symbols": set(),
            "exchange": "NSE",
            "last_validated": (),
            "last_missing": (),
        }
        initial = websocket.query_params.get("symbols")
        if initial:
            state["symbols"] = {
                s.strip().upper() for s in initial.split(",") if s.strip()
            }
        exchange = websocket.query_params.get("exchange")
        if exchange:
            state["exchange"] = exchange.upper()

        sender = asyncio.create_task(self._send_loop(websocket, state))
        try:
            await self._report_unknown(websocket, state)
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                action = msg.get("action")
                if action == "subscribe":
                    state["symbols"] = {
                        s.strip().upper()
                        for s in msg.get("symbols", [])
                        if s.strip()
                    }
                    state["exchange"] = str(
                        msg.get("exchange", state["exchange"])
                    ).upper()
                    await self._report_unknown(websocket, state)
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()

    async def _report_unknown(self, websocket: WebSocket, state: dict[str, Any]) -> None:
        if self.validate_symbols is None:
            return
        symbols = sorted(state["symbols"])
        if tuple(symbols) == state["last_validated"]:
            return
        state["last_validated"] = tuple(symbols)
        if not symbols:
            return
        missing = await self.validate_symbols(symbols, state["exchange"])
        state["last_missing"] = tuple(missing)
        if missing:
            await websocket.send_json(
                {
                    "type": "error",
                    "code": "unknown_symbols",
                    "exchange": state["exchange"],
                    "detail": (
                        f"Unknown {state['exchange']} symbols: "
                        + ", ".join(missing)
                        + "."
                    ),
                    "symbols": missing,
                }
            )

    async def _send_loop(
        self, websocket: WebSocket, state: dict[str, Any]
    ) -> None:
        while True:
            await asyncio.sleep(self.interval)
            symbols = list(state["symbols"])
            if not symbols:
                continue
            exchange = state["exchange"]
            try:
                quotes = await self.data_service.get_quotes(symbols, exchange)
            except Exception:
                quotes = []
            try:
                await websocket.send_json(
                    {
                        "type": "quotes",
                        "exchange": exchange,
                        "data": [_quote_to_json(q) for q in quotes],
                    }
                )
            except Exception:
                return
