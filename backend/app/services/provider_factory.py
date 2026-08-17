"""Selects the market-data provider from configuration.

The provider abstraction guarantees `is_mock` is always surfaced so simulated
data can never be mistaken for a live feed. If a live provider is requested
but its credentials are missing, we fail safe to the mock provider (which is
still explicitly labelled as mock) rather than crashing the API.
"""

import logging

from app.core.config import settings
from app.services.market_data import MarketDataProvider, MockMarketDataProvider
from app.services.upstox import UpstoxMarketDataProvider

logger = logging.getLogger(__name__)


def get_provider() -> MarketDataProvider:
    provider = (settings.MARKET_DATA_PROVIDER or "mock").lower()
    if provider == "upstox":
        if settings.UPSTOX_API_KEY and settings.UPSTOX_ACCESS_TOKEN:
            logger.info("market data provider: upstox (live)")
            return UpstoxMarketDataProvider(
                api_key=settings.UPSTOX_API_KEY,
                access_token=settings.UPSTOX_ACCESS_TOKEN,
                base_url=settings.UPSTOX_BASE_URL,
            )
        logger.warning(
            "MARKET_DATA_PROVIDER=upstox but UPSTOX_API_KEY/UPSTOX_ACCESS_TOKEN "
            "are not set; falling back to the mock provider"
        )
    logger.info("market data provider: mock")
    return MockMarketDataProvider()
