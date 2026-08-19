from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/execution")
async def get_execution_settings(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Server-side execution configuration surfaced to the Settings UI.

    Only non-secret knobs are exposed: whether live portfolios are permitted,
    and which broker/market-data adapter is configured. Broker credentials are
    never returned.
    """
    broker = settings.BROKER_ADAPTER.lower()
    market_data = settings.MARKET_DATA_PROVIDER.lower()
    return {
        "live_execution_enabled": settings.LIVE_EXECUTION_ENABLED,
        "broker_adapter": broker,
        "broker_is_mock": broker == "mock",
        "market_data_provider": market_data,
        "market_data_is_mock": market_data == "mock",
    }
