from tests.helpers import auth_headers, register_user

MARKET_URL = "/api/v1/market/quotes"


def _login(client, email: str) -> dict:
    tokens = register_user(client, email)
    return auth_headers(tokens)


class TestMarketQuotes:
    def test_quotes_for_seeded_symbols(self, client, seeded_instruments):
        headers = _login(client, "market1@example.com")
        res = client.get(
            MARKET_URL, params={"symbols": "RELIANCE,TCS"}, headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        symbols = {q["symbol"] for q in data}
        assert symbols == {"RELIANCE", "TCS"}
        for q in data:
            assert q["exchange"] == "NSE"
            assert q["is_mock"] is True
            assert q["source"] == "mock"
            assert q["last_price"] is not None

    def test_quotes_deterministic_within_bucket(self, client, seeded_instruments):
        headers = _login(client, "market2@example.com")
        first = client.get(
            MARKET_URL, params={"symbols": "GOLD", "exchange": "MCX"}, headers=headers
        ).json()[0]
        second = client.get(
            MARKET_URL, params={"symbols": "GOLD", "exchange": "MCX"}, headers=headers
        ).json()[0]
        assert first["last_price"] == second["last_price"]

    def test_unknown_symbol_returns_404(self, client, seeded_instruments):
        headers = _login(client, "market3@example.com")
        res = client.get(
            MARKET_URL, params={"symbols": "NOTAREALSYMBOL"}, headers=headers
        )
        assert res.status_code == 404
        assert "NOTAREALSYMBOL" in res.json()["detail"]

    def test_too_many_symbols_returns_400(self, client, seeded_instruments):
        headers = _login(client, "market4@example.com")
        symbols = ",".join(f"SYM{i}" for i in range(51))
        res = client.get(MARKET_URL, params={"symbols": symbols}, headers=headers)
        assert res.status_code == 400

    def test_requires_auth(self, client, seeded_instruments):
        res = client.get(MARKET_URL, params={"symbols": "RELIANCE"})
        assert res.status_code == 401
