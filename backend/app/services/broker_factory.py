"""Selects the broker execution adapter from configuration.

Mirrors ``provider_factory``: if a live broker adapter is requested but its
credentials are missing, we fail safe to the mock adapter (still explicitly
labelled ``is_mock = true``) rather than crashing or mislabelling execution.
"""

import logging

from app.core.config import settings
from app.services.broker import BrokerAdapter, MockBrokerAdapter
from app.services.upstox_broker import UpstoxBrokerAdapter

logger = logging.getLogger(__name__)


def get_broker() -> BrokerAdapter:
    adapter = (settings.BROKER_ADAPTER or "mock").lower()
    if adapter == "upstox":
        if settings.UPSTOX_API_KEY and settings.UPSTOX_ACCESS_TOKEN:
            logger.info("broker adapter: upstox (live)")
            return UpstoxBrokerAdapter(
                api_key=settings.UPSTOX_API_KEY,
                access_token=settings.UPSTOX_ACCESS_TOKEN,
                base_url=settings.UPSTOX_BASE_URL,
                product=settings.UPSTOX_BROKER_PRODUCT,
            )
        logger.warning(
            "BROKER_ADAPTER=upstox but UPSTOX_API_KEY/UPSTOX_ACCESS_TOKEN "
            "are not set; falling back to the mock broker adapter"
        )
    logger.info("broker adapter: mock")
    return MockBrokerAdapter()
