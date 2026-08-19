from tests.helpers import auth_headers, register_user

PORTFOLIOS_URL = "/api/v1/portfolios"


def _create_portfolio(client, headers: dict, name: str = "Main") -> dict:
    res = client.post(
        PORTFOLIOS_URL,
        headers=headers,
        json={"name": name, "initial_capital": "100000.00"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _strategies_url(portfolio_id: str) -> str:
    return f"{PORTFOLIOS_URL}/{portfolio_id}/strategies"


def _create_strategy(client, headers: dict, portfolio_id: str, name: str = "RSI") -> dict:
    res = client.post(
        _strategies_url(portfolio_id),
        headers=headers,
        json={
            "name": name,
            "description": "test strategy",
            "strategy_type": "rsi",
            "parameters": {"period": 14},
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


class TestStrategyCrud:
    def test_create_and_list(self, client):
        tokens = register_user(client, "strat1@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        created = _create_strategy(client, headers, portfolio["id"])

        res = client.get(_strategies_url(portfolio["id"]), headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == created["id"]
        assert data[0]["name"] == "RSI"
        assert data[0]["strategy_type"] == "rsi"
        assert data[0]["status"] == "active"
        assert data[0]["parameters"] == {"period": 14}
        assert data[0]["portfolio_id"] == portfolio["id"]

    def test_get(self, client):
        tokens = register_user(client, "strat2@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        created = _create_strategy(client, headers, portfolio["id"])

        res = client.get(
            f"{_strategies_url(portfolio['id'])}/{created['id']}",
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["name"] == "RSI"

    def test_update(self, client):
        tokens = register_user(client, "strat3@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        created = _create_strategy(client, headers, portfolio["id"])

        res = client.patch(
            f"{_strategies_url(portfolio['id'])}/{created['id']}",
            headers=headers,
            json={
                "name": "Renamed",
                "description": "edited",
                "status": "inactive",
                "strategy_type": "ema_crossover",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "Renamed"
        assert body["description"] == "edited"
        assert body["status"] == "inactive"
        assert body["strategy_type"] == "ema_crossover"

    def test_delete(self, client):
        tokens = register_user(client, "strat4@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        created = _create_strategy(client, headers, portfolio["id"])

        res = client.delete(
            f"{_strategies_url(portfolio['id'])}/{created['id']}",
            headers=headers,
        )
        assert res.status_code == 204

        res = client.get(_strategies_url(portfolio["id"]), headers=headers)
        assert res.json() == []

    def test_duplicate_name_conflict_within_portfolio(self, client):
        tokens = register_user(client, "strat5@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        _create_strategy(client, headers, portfolio["id"], name="Solo")

        res = client.post(
            _strategies_url(portfolio["id"]),
            headers=headers,
            json={"name": "Solo"},
        )
        assert res.status_code == 409

    def test_same_name_allowed_in_different_portfolios(self, client):
        tokens = register_user(client, "strat6@example.com")
        headers = auth_headers(tokens)
        p1 = _create_portfolio(client, headers, name="P1")
        p2 = _create_portfolio(client, headers, name="P2")
        _create_strategy(client, headers, p1["id"], name="Shared")
        res = client.post(
            _strategies_url(p2["id"]),
            headers=headers,
            json={"name": "Shared"},
        )
        assert res.status_code == 201

    def test_filter_by_status(self, client):
        tokens = register_user(client, "strat7@example.com")
        headers = auth_headers(tokens)
        portfolio = _create_portfolio(client, headers)
        created = _create_strategy(client, headers, portfolio["id"])

        res = client.get(
            _strategies_url(portfolio["id"]) + "?status=archived",
            headers=headers,
        )
        assert res.json() == []

        res = client.get(
            _strategies_url(portfolio["id"]) + "?status=active",
            headers=headers,
        )
        assert len(res.json()) == 1
        assert res.json()[0]["id"] == created["id"]


class TestStrategyScoping:
    def test_strategy_not_visible_via_other_portfolio(self, client):
        tokens = register_user(client, "strat8@example.com")
        headers = auth_headers(tokens)
        p1 = _create_portfolio(client, headers, name="P1")
        p2 = _create_portfolio(client, headers, name="P2")
        created = _create_strategy(client, headers, p1["id"])

        res = client.get(
            f"{_strategies_url(p2['id'])}/{created['id']}",
            headers=headers,
        )
        assert res.status_code == 404


class TestStrategyTenantIsolation:
    def test_user_cannot_access_other_users_strategies(self, client):
        a_tokens = register_user(client, "strat9@example.com")
        b_tokens = register_user(client, "strat10@example.com")
        other = _create_portfolio(client, auth_headers(a_tokens))
        created = _create_strategy(client, auth_headers(a_tokens), other["id"])
        other_id = other["id"]

        res = client.get(
            _strategies_url(other_id), headers=auth_headers(b_tokens)
        )
        assert res.status_code == 404

        res = client.post(
            _strategies_url(other_id),
            headers=auth_headers(b_tokens),
            json={"name": "Hijacked"},
        )
        assert res.status_code == 404

        res = client.patch(
            f"{_strategies_url(other_id)}/{created['id']}",
            headers=auth_headers(b_tokens),
            json={"name": "Hijacked"},
        )
        assert res.status_code == 404

        res = client.delete(
            f"{_strategies_url(other_id)}/{created['id']}",
            headers=auth_headers(b_tokens),
        )
        assert res.status_code == 404

        # Owner still sees their strategy.
        res = client.get(
            _strategies_url(other_id), headers=auth_headers(a_tokens)
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_auth_required(self, client):
        res = client.get(_strategies_url("00000000-0000-0000-0000-000000000000"))
        assert res.status_code == 401
