from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import rate_limit_dependency
from app.domain.enums import Exchange
from app.models.user import User
from app.repositories.instruments import InstrumentRepository
from app.schemas.market import Quote
from app.services.market_data import mock_market_data_service

router = APIRouter(prefix="/market", tags=["market"])

quotes_rate_limit = rate_limit_dependency("market:quotes", 60, 60)
MAX_SYMBOLS = 50


@router.get(
    "/quotes",
    response_model=list[Quote],
    dependencies=[Depends(quotes_rate_limit)],
)
async def get_quotes(
    symbols: str = Query(min_length=1, max_length=1000),
    exchange: Exchange = Exchange.NSE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    symbol_list = [
        s.strip().upper() for s in symbols.split(",") if s.strip()
    ]
    if not symbol_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No symbols provided.",
        )
    if len(symbol_list) > MAX_SYMBOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many symbols (max {MAX_SYMBOLS}).",
        )

    repo = InstrumentRepository(db)
    existing = {
        s: repo.get_by_exchange_symbol(exchange.value, s) for s in symbol_list
    }
    missing = [s for s, instr in existing.items() if instr is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown {exchange.value} symbols: {', '.join(missing)}.",
        )

    quotes = await mock_market_data_service.get_quotes(symbol_list, exchange.value)
    return quotes
