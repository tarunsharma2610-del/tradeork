"""Selects the broker execution adapter from configuration or the user.

Mirrors ``provider_factory``: if a live broker adapter is requested but its
credentials are missing, we fail safe to the mock adapter (still explicitly
labelled ``is_mock = true``) rather than crashing or mislabelling execution.

Per-user connections take precedence: when a user has stored their own Upstox
credentials (Settings → broker connections), their live orders run through
*their* account via :func:`get_broker_for_user`, falling back to the
server-configured ``get_broker`` only when no connection exists.
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.broker import BrokerAdapter, MockBrokerAdapter
from app.services.broker_connections import BrokerConnectionService
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


def get_broker_for_user(db: Session, user_id: UUID) -> BrokerAdapter:
    """Resolve the execution adapter for a user's live portfolio.

    Preference order:
    1. The user's stored broker connection (their own Upstox account).
    2. The server-configured adapter (``BROKER_ADAPTER`` env / mock).
    """
    adapter = BrokerConnectionService(db).resolve_adapter(user_id)
    if adapter is not None:
        logger.info("broker adapter for user %s: upstox (live, per-user)", user_id)
        return adapter
    return get_broker()
