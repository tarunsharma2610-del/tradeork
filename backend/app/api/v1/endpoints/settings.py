from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.broker_connections import BrokerConnectionRepository

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/execution")
async def get_execution_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Server-side execution configuration surfaced to the Settings UI.

    Only non-secret knobs are exposed: whether live portfolios are permitted,
    which broker/market-data adapter is configured, and whether the current
    user has stored their own broker credentials. Broker credentials are
    never returned.
    """
    broker = settings.BROKER_ADAPTER.lower()
    market_data = settings.MARKET_DATA_PROVIDER.lower()
    connections = BrokerConnectionRepository(db).list_for_user(current_user.id)
    active_upstox = any(
        c.provider == "upstox" and c.is_active for c in connections
    )
    return {
        "live_execution_enabled": settings.LIVE_EXECUTION_ENABLED,
        "broker_adapter": broker,
        "broker_is_mock": broker == "mock",
        "broker_connected": active_upstox,
        "market_data_provider": market_data,
        "market_data_is_mock": market_data == "mock",
    }
