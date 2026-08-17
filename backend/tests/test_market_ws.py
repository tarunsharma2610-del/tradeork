import time

import pytest
from starlette.websockets import WebSocketDisconnect

from tests.helpers import register_user


def test_market_ws_rejects_missing_token(client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/market/ws"):
            pass
    assert exc_info.value.code == 4401


def test_market_ws_rejects_invalid_token(client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/market/ws?token=garbage"):
            pass
    assert exc_info.value.code == 4401


def test_market_ws_ping_pong(client, seeded_instruments):
    tokens = register_user(client, "ws1@example.com")
    token = tokens["access_token"]
    with client.websocket_connect(
        f"/api/v1/market/ws?token={token}&symbols=RELIANCE&exchange=NSE"
    ) as ws:
        ws.send_json({"action": "ping"})
        msg = ws.receive_json()
        assert msg == {"type": "pong"}


def test_market_ws_streams_mock_quotes(client, seeded_instruments):
    tokens = register_user(client, "ws2@example.com")
    token = tokens["access_token"]
    with client.websocket_connect(
        f"/api/v1/market/ws?token={token}&symbols=RELIANCE&exchange=NSE"
    ) as ws:
        ws.send_json({"action": "ping"})
        ws.receive_json()  # consume pong
        # First quote message arrives after MARKET_DATA_POLL_INTERVAL (2s default)
        deadline = time.time() + 15
        msg = None
        while time.time() < deadline:
            msg = ws.receive_json()
            if msg.get("type") == "quotes":
                break
        assert msg and msg["type"] == "quotes"
        assert msg["exchange"] == "NSE"
        assert len(msg["data"]) == 1
        q = msg["data"][0]
        assert q["symbol"] == "RELIANCE"
        assert q["is_mock"] is True
        assert q["source"] == "mock"


def test_market_ws_reports_unknown_symbols(client, seeded_instruments):
    tokens = register_user(client, "ws3@example.com")
    token = tokens["access_token"]
    with client.websocket_connect(
        f"/api/v1/market/ws?token={token}&symbols=RELIANCE,ZZZZ&exchange=NSE"
    ) as ws:
        deadline = time.time() + 10
        msg = None
        while time.time() < deadline:
            msg = ws.receive_json()
            if msg.get("type") == "error":
                break
        assert msg and msg["type"] == "error"
        assert msg["code"] == "unknown_symbols"
        assert msg["symbols"] == ["ZZZZ"]
        assert "ZZZZ" in msg["detail"]


def test_market_ws_resubscribe_validates_again(client, seeded_instruments):
    tokens = register_user(client, "ws4@example.com")
    token = tokens["access_token"]
    with client.websocket_connect(
        f"/api/v1/market/ws?token={token}&symbols=RELIANCE&exchange=NSE"
    ) as ws:
        ws.send_json({"action": "subscribe", "symbols": ["INFY", "NOPE"], "exchange": "NSE"})
        deadline = time.time() + 10
        msg = None
        while time.time() < deadline:
            msg = ws.receive_json()
            if msg.get("type") == "error":
                break
        assert msg and msg["type"] == "error"
        assert msg["symbols"] == ["NOPE"]
