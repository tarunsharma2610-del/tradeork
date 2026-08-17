"""WebSocket quote streaming for a single client.

A background task periodically fetches quotes for the client's current
subscription through the same MarketDataService (and provider) as the REST
endpoint, and pushes them as JSON messages. Redis-cached quotes make the
poll interval cheap even with many connected clients.
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.services.market_data import MarketDataService, _quote_to_json


class QuoteStreamService:
    """Streams quotes to one WebSocket client.

    The client may subscribe via query parameters on connect
    (``symbols``, ``exchange``) and/or at any time via messages:
    ``{"action": "subscribe", "symbols": [...], "exchange": "NSE"}``.
    """

    def __init__(self, data_service: MarketDataService, interval: float = 2.0) -> None:
        self.data_service = data_service
        self.interval = interval

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        state: dict[str, Any] = {"symbols": set(), "exchange": "NSE"}
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
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()

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
