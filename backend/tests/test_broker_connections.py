import uuid

import pytest

from app.core.config import settings
from app.core.security import decrypt_secret, encrypt_secret
from app.repositories.broker_connections import BrokerConnectionRepository
from tests.helpers import auth_headers, register_user

BROKER_URL = "/api/v1/settings/broker"
EXECUTION_URL = "/api/v1/settings/execution"

TOKEN = "0123456789abcdef0123456789abcdef"  # fake but plausible length
API_KEY = "client-id-123"
PORTFOLIOS_URL = "/api/v1/portfolios"


def _create(client, headers, **overrides):
    payload = {"provider": "upstox", "access_token": TOKEN, "api_key": API_KEY}
    payload.update(overrides)
    return client.post(BROKER_URL, headers=headers, json=payload)


class TestBrokerConnectionApi:
    def test_auth_required(self, client):
        assert client.get(BROKER_URL).status_code == 401
        assert (
            client.post(BROKER_URL, json={"access_token": TOKEN}).status_code
            == 401
        )
        assert (
            client.patch(
                f"{BROKER_URL}/00000000-0000-0000-0000-000000000000",
                json={},
            ).status_code
            == 401
        )
        assert (
            client.delete(
                f"{BROKER_URL}/00000000-0000-0000-0000-000000000000"
            ).status_code
            == 401
        )

    def test_create_returns_masked_only(self, client):
        headers = auth_headers(register_user(client, "broker@example.com"))
        res = _create(client, headers)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["provider"] == "upstox"
        assert body["access_token_masked"] == "****cdef"
        assert body["api_key_masked"] == "****-123"
        assert "access_token" not in body
        assert "api_key" not in body
        assert body["is_active"] is True

    def test_token_encrypted_at_rest(self, client, db_session):
        headers = auth_headers(register_user(client, "broker2@example.com"))
        res = _create(client, headers)
        assert res.status_code == 201, res.text
        body = res.json()
        stored = BrokerConnectionRepository(db_session).get_for_user(
            uuid.UUID(body["user_id"]), uuid.UUID(body["id"])
        )
        assert stored is not None
        assert stored.access_token_encrypted != TOKEN
        assert decrypt_secret(stored.access_token_encrypted) == TOKEN
        assert decrypt_secret(stored.api_key_encrypted) == API_KEY

    def test_list_masked_and_tenant_scoped(self, client):
        headers = auth_headers(register_user(client, "broker3@example.com"))
        _create(client, headers)
        other_headers = auth_headers(
            register_user(client, "broker-other@example.com")
        )
        res = client.get(BROKER_URL, headers=other_headers)
        assert res.status_code == 200
        assert res.json() == []
        mine = client.get(BROKER_URL, headers=headers)
        assert len(mine.json()) == 1
        assert mine.json()[0]["access_token_masked"] == "****cdef"

    def test_update_token_and_label(self, client):
        headers = auth_headers(register_user(client, "broker4@example.com"))
        conn = _create(client, headers).json()
        new_token = "fedcba9876543210fedcba9876543210"
        res = client.patch(
            f"{BROKER_URL}/{conn['id']}",
            headers=headers,
            json={"access_token": new_token, "label": "My main Upstox"},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["label"] == "My main Upstox"
        assert body["access_token_masked"] == "****3210"
        assert body["api_key_masked"] == "****-123"

    def test_deactivate_and_delete(self, client):
        headers = auth_headers(register_user(client, "broker5@example.com"))
        conn = _create(client, headers).json()
        res = client.patch(
            f"{BROKER_URL}/{conn['id']}",
            headers=headers,
            json={"is_active": False},
        )
        assert res.status_code == 200, res.text
        assert res.json()["is_active"] is False
        res = client.delete(f"{BROKER_URL}/{conn['id']}", headers=headers)
        assert res.status_code == 204
        assert client.get(BROKER_URL, headers=headers).json() == []

    def test_ownership_enforced(self, client):
        headers = auth_headers(register_user(client, "broker6@example.com"))
        conn = _create(client, headers).json()
        other = auth_headers(register_user(client, "broker-other2@example.com"))
        assert (
            client.patch(
                f"{BROKER_URL}/{conn['id']}",
                headers=other,
                json={"label": "hijack"},
            ).status_code
            == 404
        )
        assert (
            client.delete(f"{BROKER_URL}/{conn['id']}", headers=other).status_code
            == 404
        )

    def test_max_connections_per_user(self, client):
        headers = auth_headers(register_user(client, "broker-max@example.com"))
        for i in range(5):
            res = _create(client, headers, access_token=f"{TOKEN}{i}")
            assert res.status_code == 201, res.text
        res = _create(client, headers, access_token=f"{TOKEN}9")
        assert res.status_code == 409, res.text

    def test_short_token_rejected(self, client):
        headers = auth_headers(register_user(client, "broker-short@example.com"))
        res = _create(client, headers, access_token="short")
        assert res.status_code == 422, res.text


class TestExecutionSettingsBrokerConnected:
    def test_broker_connected_reflects_user_connection(self, client):
        headers = auth_headers(register_user(client, "broker-exec@example.com"))
        res = client.get(EXECUTION_URL, headers=headers)
        assert res.status_code == 200
        assert res.json()["broker_connected"] is False
        _create(client, headers)
        res = client.get(EXECUTION_URL, headers=headers)
        assert res.json()["broker_connected"] is True


class TestLiveExecutionViaStoredConnection:
    """A live portfolio routes through the user's stored Upstox credentials."""

    @pytest.fixture()
    def live_enabled(self, monkeypatch):
        monkeypatch.setattr(settings, "LIVE_EXECUTION_ENABLED", True)
        return monkeypatch

    def test_live_order_uses_stored_connection(
        self, client, seeded_instruments, live_enabled, monkeypatch
    ):
        import app.services.broker_connections as bc_module
        from tests.test_live_execution import FakeLiveBroker

        broker = FakeLiveBroker()
        monkeypatch.setattr(
            bc_module, "UpstoxBrokerAdapter", lambda **kwargs: broker
        )
        headers = auth_headers(register_user(client, "stored-live@example.com"))
        conn = _create(client, headers, access_token=TOKEN).json()
        assert conn["access_token_masked"] == "****cdef"

        portfolio = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        ).json()
        inst = client.get(
            "/api/v1/instruments",
            params={"q": "RELIANCE", "exchange": "NSE", "instrument_type": "EQUITY"},
        ).json()[0]
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 5,
            },
        )
        assert res.status_code == 201, res.text
        order = res.json()
        assert order["execution_mode"] == "live"
        assert order["status"] == "filled"
        assert order["broker_order_id"] is not None
        # The request reached the user-scoped adapter, not the mock.
        assert len(broker.placed) == 1
        assert broker.placed[0].symbol == "RELIANCE"

    def test_live_order_without_connection_rejected(
        self, client, seeded_instruments, live_enabled
    ):
        headers = auth_headers(register_user(client, "no-conn@example.com"))
        portfolio = client.post(
            PORTFOLIOS_URL,
            headers=headers,
            json={
                "name": "Live",
                "initial_capital": "100000.00",
                "execution_mode": "live",
            },
        ).json()
        inst = client.get(
            "/api/v1/instruments",
            params={"q": "RELIANCE", "exchange": "NSE", "instrument_type": "EQUITY"},
        ).json()[0]
        res = client.post(
            f"{PORTFOLIOS_URL}/{portfolio['id']}/orders",
            headers=headers,
            json={
                "instrument_id": inst["id"],
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 5,
            },
        )
        assert res.status_code == 400, res.text
        assert "Settings" in res.json()["detail"]


class TestEncryptDecryptHelpers:
    def test_roundtrip(self):
        original = "some-secret-token"
        cipher = encrypt_secret(original)
        assert cipher != original
        assert decrypt_secret(cipher) == original
        assert decrypt_secret(encrypt_secret(original)) == original
