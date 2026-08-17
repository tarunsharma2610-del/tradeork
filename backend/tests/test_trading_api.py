import uuid

from tests.helpers import auth_headers, register_user

PORTFOLIOS_URL = "/api/v1/portfolios"


def _create_portfolio(client, headers: dict, capital: str = "100000.00") -> dict:
    res = client.post(
        PORTFOLIOS_URL,
        headers=headers,
        json={"name": "Main", "initial_capital": capital, "currency": "INR"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _reliance_equity(client) -> dict:
    res = client.get(
        "/api/v1/instruments",
        params={"q": "RELIANCE", "exchange": "NSE", "instrument_type": "EQUITY"},
    )
    assert res.status_code == 200
    return res.json()[0]


class TestTradingApi:
    def test_place_market_order_creates_position(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade1@example.com"))
        portfolio = _create_portfolio(client, headers, capital="1000000.00")
        inst = _reliance_equity(client)

        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 10,
            },
        )
        assert res.status_code == 201, res.text
        order = res.json()
        assert order["status"] == "filled"
        assert order["filled_quantity"] == 10
        assert order["symbol"] == "RELIANCE"
        assert order["avg_fill_price"] is not None

        pos = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/positions", headers=headers
        ).json()
        assert len(pos) == 1
        assert pos[0]["quantity"] == 10
        assert pos[0]["symbol"] == "RELIANCE"
        assert pos[0]["realized_pnl"] == "0.00"

    def test_limit_order_pending_then_cancel(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade2@example.com"))
        portfolio = _create_portfolio(client, headers)
        inst = _reliance_equity(client)

        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 10,
                "limit_price": "0.01",
            },
        )
        assert res.status_code == 201, res.text
        order = res.json()
        assert order["status"] == "pending"

        cancel = client.delete(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders/{order['id']}",
            headers=headers,
        )
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

    def test_insufficient_cash_rejected(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade3@example.com"))
        portfolio = _create_portfolio(client, headers, capital="100.00")
        inst = _reliance_equity(client)

        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 1000,
            },
        )
        assert res.status_code == 201
        body = res.json()
        assert body["status"] == "rejected"
        assert "Insufficient cash" in body["reject_reason"]

    def test_summary_endpoint(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade4@example.com"))
        portfolio = _create_portfolio(client, headers, capital="1000000.00")
        inst = _reliance_equity(client)
        client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 10,
            },
        )
        res = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/summary", headers=headers
        )
        assert res.status_code == 200
        body = res.json()
        assert body["positions_count"] == 1
        assert body["open_orders_count"] == 0
        assert body["equity"] is not None

    def test_orders_list_filter(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade5@example.com"))
        portfolio = _create_portfolio(client, headers, capital="1000000.00")
        inst = _reliance_equity(client)
        client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 5,
            },
        )
        res = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            params={"status": "filled"},
            headers=headers,
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_requires_auth(self, client, seeded_instruments):
        res = client.get(f"{PORTFOLIOS_URL}/{uuid.uuid4()}/positions")
        assert res.status_code == 401

    def test_tenant_isolation(self, client, seeded_instruments):
        a_headers = auth_headers(register_user(client, "trade6@example.com"))
        portfolio = _create_portfolio(client, a_headers, capital="1000000.00")
        b_headers = auth_headers(register_user(client, "trade7@example.com"))

        res = client.get(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/positions", headers=b_headers
        )
        assert res.status_code == 404
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=b_headers,
            json={
                "instrument_id": _reliance_equity(client)["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 1,
            },
        )
        assert res.status_code == 404

    def test_limit_order_requires_limit_price(self, client, seeded_instruments):
        headers = auth_headers(register_user(client, "trade8@example.com"))
        portfolio = _create_portfolio(client, headers)
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": _reliance_equity(client)["id"],
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 10,
            },
        )
        assert res.status_code == 422
