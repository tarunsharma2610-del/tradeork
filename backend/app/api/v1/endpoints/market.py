from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import authenticate_token, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit_dependency
from app.domain.enums import Exchange
from app.repositories.instruments import InstrumentRepository
from app.schemas.market import Quote
from app.services.market_data import MarketDataService
from app.services.provider_factory import get_provider
from app.services.quote_stream import QuoteStreamService

router = APIRouter(prefix="/market", tags=["market"])

quotes_rate_limit = rate_limit_dependency("market:quotes", 60, 60)
MAX_SYMBOLS = 50

market_data_service = MarketDataService(get_provider())


@router.get(
    "/quotes",
    response_model=list[Quote],
    dependencies=[Depends(quotes_rate_limit)],
)
async def get_quotes(
    symbols: str = Query(min_length=1, max_length=1000),
    exchange: Exchange = Exchange.NSE,
    current_user=Depends(get_current_user),
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

    quotes = await market_data_service.get_quotes(symbol_list, exchange.value)
    return quotes


@router.websocket("/ws")
async def market_quotes_stream(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    """Stream quotes to an authenticated client over WebSocket.

    Auth is via ``?token=<access JWT>`` (browsers cannot set headers on
    WebSocket connections). Optionally pass ``symbols``/``exchange`` query
    params for an initial subscription; the client can re-subscribe at any
    time with ``{"action": "subscribe", ...}`` messages.
    """
    token = websocket.query_params.get("token")
    if authenticate_token(token or "", db) is None:
        await websocket.close(code=4401)
        return

    async def validate_symbols(
        symbols: list[str], exchange: str
    ) -> list[str]:
        repo = InstrumentRepository(db)
        return [
            s
            for s in symbols
            if repo.get_by_exchange_symbol(exchange, s) is None
        ]

    stream = QuoteStreamService(
        market_data_service,
        interval=settings.MARKET_DATA_POLL_INTERVAL,
        validate_symbols=validate_symbols,
    )
    await stream.handle(websocket)
