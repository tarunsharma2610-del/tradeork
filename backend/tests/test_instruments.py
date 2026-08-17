INSTRUMENTS_URL = "/api/v1/instruments"


class TestInstrumentSearch:
    def test_list_all(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 50
        assert all(item["is_active"] for item in data)

    def test_search_by_query(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"q": "reliance"})
        assert res.status_code == 200
        symbols = [item["symbol"] for item in res.json()]
        assert "RELIANCE" in symbols

    def test_filter_by_exchange(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"exchange": "MCX"})
        assert res.status_code == 200
        assert all(item["exchange"] == "MCX" for item in res.json())
        assert any(item["symbol"] == "GOLD" for item in res.json())

    def test_filter_by_instrument_type(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"instrument_type": "OPTION"})
        assert res.status_code == 200
        assert all(item["instrument_type"] == "OPTION" for item in res.json())

    def test_limit(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"limit": 5})
        assert res.status_code == 200
        assert len(res.json()) == 5

    def test_limit_too_large_rejected(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"limit": 500})
        assert res.status_code == 422

    def test_get_by_id(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"q": "TCS", "exchange": "NSE"})
        instrument = res.json()[0]

        res = client.get(f"{INSTRUMENTS_URL}/{instrument['id']}")
        assert res.status_code == 200
        body = res.json()
        assert body["symbol"] == "TCS"
        assert body["exchange"] == "NSE"

    def test_get_missing_returns_404(self, client, seeded_instruments):
        res = client.get(f"{INSTRUMENTS_URL}/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    def test_unknown_exchange_rejected(self, client, seeded_instruments):
        res = client.get(INSTRUMENTS_URL, params={"exchange": "NASDAQ"})
        assert res.status_code == 422
