from tests.helpers import auth_headers, register_user

SETTINGS_URL = "/api/v1/settings/execution"


class TestExecutionSettings:
    def test_auth_required(self, client):
        res = client.get(SETTINGS_URL)
        assert res.status_code == 401

    def test_returns_default_config(self, client):
        tokens = register_user(client, "settings@example.com")
        res = client.get(SETTINGS_URL, headers=auth_headers(tokens))
        assert res.status_code == 200
        body = res.json()
        assert body["live_execution_enabled"] is False
        assert body["broker_adapter"] == "mock"
        assert body["broker_is_mock"] is True
        assert body["market_data_provider"] == "mock"
        assert body["market_data_is_mock"] is True

    def test_reflects_configured_adapters(self, client, monkeypatch):
        from app.core.config import settings

        original_broker = settings.BROKER_ADAPTER
        original_market = settings.MARKET_DATA_PROVIDER
        original_live = settings.LIVE_EXECUTION_ENABLED
        settings.BROKER_ADAPTER = "upstox"
        settings.MARKET_DATA_PROVIDER = "upstox"
        settings.LIVE_EXECUTION_ENABLED = True
        try:
            tokens = register_user(client, "settings2@example.com")
            res = client.get(SETTINGS_URL, headers=auth_headers(tokens))
            assert res.status_code == 200
            body = res.json()
            assert body["live_execution_enabled"] is True
            assert body["broker_adapter"] == "upstox"
            assert body["broker_is_mock"] is False
            assert body["market_data_provider"] == "upstox"
            assert body["market_data_is_mock"] is False
        finally:
            settings.BROKER_ADAPTER = original_broker
            settings.MARKET_DATA_PROVIDER = original_market
            settings.LIVE_EXECUTION_ENABLED = original_live
