from tests.helpers import auth_headers, register_user

PORTFOLIOS_URL = "/api/v1/portfolios"


def _create_portfolio(client, headers: dict, name: str = "Main") -> dict:
    res = client.post(
        PORTFOLIOS_URL,
        headers=headers,
        json={
            "name": name,
            "description": "test portfolio",
            "initial_capital": "100000.00",
            "currency": "INR",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


class TestPortfolioCrud:
    def test_create_and_list(self, client):
        tokens = register_user(client, "alice@example.com")
        headers = auth_headers(tokens)
        created = _create_portfolio(client, headers)

        res = client.get(PORTFOLIOS_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == created["id"]
        assert data[0]["name"] == "Main"
        assert data[0]["initial_capital"] == "100000.00"
        assert data[0]["currency"] == "INR"
        assert data[0]["status"] == "active"

    def test_get(self, client):
        tokens = register_user(client, "bob@example.com")
        headers = auth_headers(tokens)
        created = _create_portfolio(client, headers)

        res = client.get(f"{PORTFOLIOS_URL}/{created['id']}", headers=headers)
        assert res.status_code == 200
        assert res.json()["name"] == "Main"

    def test_update(self, client):
        tokens = register_user(client, "carol@example.com")
        headers = auth_headers(tokens)
        created = _create_portfolio(client, headers)

        res = client.patch(
            f"{PORTFOLIOS_URL}/{created['id']}",
            headers=headers,
            json={"name": "Renamed", "initial_capital": "250000.00"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "Renamed"
        assert body["initial_capital"] == "250000.00"

    def test_delete(self, client):
        tokens = register_user(client, "dave@example.com")
        headers = auth_headers(tokens)
        created = _create_portfolio(client, headers)

        res = client.delete(f"{PORTFOLIOS_URL}/{created['id']}", headers=headers)
        assert res.status_code == 204

        res = client.get(f"{PORTFOLIOS_URL}/{created['id']}", headers=headers)
        assert res.status_code == 404

    def test_duplicate_name_conflict(self, client):
        tokens = register_user(client, "erin@example.com")
        headers = auth_headers(tokens)
        _create_portfolio(client, headers, name="Solo")

        res = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={"name": "Solo", "initial_capital": "100.00"},
        )
        assert res.status_code == 409

    def test_duplicate_name_allowed_across_users(self, client):
        a_tokens = register_user(client, "frank@example.com")
        b_tokens = register_user(client, "grace@example.com")
        _create_portfolio(client, auth_headers(a_tokens), name="Shared")
        res = client.post(
            PORTFOLIOS_URL,
            headers=auth_headers(b_tokens),
            json={"name": "Shared", "initial_capital": "100.00"},
        )
        assert res.status_code == 201


class TestPortfolioTenantIsolation:
    def test_user_cannot_read_other_users_portfolio(self, client):
        a_tokens = register_user(client, "hannah@example.com")
        b_tokens = register_user(client, "ivan@example.com")
        other = _create_portfolio(client, auth_headers(a_tokens))

        res = client.get(
            f"{PORTFOLIOS_URL}/{other['id']}",
            headers=auth_headers(b_tokens),
        )
        assert res.status_code == 404

    def test_user_cannot_update_other_users_portfolio(self, client):
        a_tokens = register_user(client, "judy@example.com")
        b_tokens = register_user(client, "ken@example.com")
        other = _create_portfolio(client, auth_headers(a_tokens))

        res = client.patch(
            f"{PORTFOLIOS_URL}/{other['id']}",
            headers=auth_headers(b_tokens),
            json={"name": "Hijacked"},
        )
        assert res.status_code == 404

    def test_user_cannot_delete_other_users_portfolio(self, client):
        a_tokens = register_user(client, "laura@example.com")
        b_tokens = register_user(client, "mike@example.com")
        other = _create_portfolio(client, auth_headers(a_tokens))

        res = client.delete(
            f"{PORTFOLIOS_URL}/{other['id']}",
            headers=auth_headers(b_tokens),
        )
        assert res.status_code == 404

        # Original owner still sees it.
        res = client.get(
            f"{PORTFOLIOS_URL}/{other['id']}",
            headers=auth_headers(a_tokens),
        )
        assert res.status_code == 200

    def test_auth_required(self, client):
        res = client.get(PORTFOLIOS_URL)
        assert res.status_code == 401
