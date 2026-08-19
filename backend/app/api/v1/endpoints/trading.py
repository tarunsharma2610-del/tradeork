from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.domain.enums import ExecutionMode
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.schemas.position import PortfolioSummary, PositionRead
from app.services.broker_factory import get_broker_for_user
from app.services.live_execution import LiveExecutionService
from app.services.paper_engine import PaperOrderEngine

router = APIRouter(prefix="/portfolios/{portfolio_id}", tags=["trading"])


def _portfolio(db: Session, portfolio_id: UUID, user_id: UUID) -> Portfolio:
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found.",
        )
    return portfolio


def _execution_for(
    db: Session, portfolio_id: UUID, user_id: UUID
) -> PaperOrderEngine | LiveExecutionService:
    """Return the execution service matching the portfolio's execution mode.

    Live portfolios resolve their broker adapter from the current user's
    stored broker connection (Settings → broker connections), falling back to
    the server-configured ``BROKER_ADAPTER``.
    """
    portfolio = _portfolio(db, portfolio_id, user_id)
    if portfolio.execution_mode == ExecutionMode.LIVE.value:
        broker = get_broker_for_user(db, user_id)
        if broker.is_mock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Live execution is not configured: add your Upstox API "
                    "in Settings, or set BROKER_ADAPTER=upstox + credentials "
                    "on the server."
                ),
            )
        return LiveExecutionService(db, broker)
    return PaperOrderEngine(db)


@router.post(
    "/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def place_order(
    portfolio_id: UUID,
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderRead:
    engine = _execution_for(db, portfolio_id, current_user.id)
    return await engine.place_order(current_user.id, portfolio_id, data)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    portfolio_id: UUID,
    order_status: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    _portfolio(db, portfolio_id, current_user.id)
    return PaperOrderEngine(db).list_orders(current_user.id, portfolio_id, order_status)


@router.delete(
    "/orders/{order_id}",
    response_model=OrderRead,
)
async def cancel_order(
    portfolio_id: UUID,
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderRead:
    engine = _execution_for(db, portfolio_id, current_user.id)
    if isinstance(engine, LiveExecutionService):
        return await engine.cancel_order(current_user.id, portfolio_id, order_id)
    return engine.cancel_order(current_user.id, portfolio_id, order_id)


@router.post(
    "/orders/{order_id}/refresh",
    response_model=OrderRead,
)
async def refresh_order_status(
    portfolio_id: UUID,
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderRead:
    """Live-only: poll the broker for the latest order state and sync the ledger."""
    engine = _execution_for(db, portfolio_id, current_user.id)
    if not isinstance(engine, LiveExecutionService):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh is only available for live orders.",
        )
    return await engine.refresh_order_status(current_user.id, portfolio_id, order_id)


@router.get("/positions", response_model=list[PositionRead])
async def list_positions(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    _portfolio(db, portfolio_id, current_user.id)
    return await PaperOrderEngine(db).list_positions(current_user.id, portfolio_id)


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _portfolio(db, portfolio_id, current_user.id)
    return await PaperOrderEngine(db).portfolio_summary(current_user.id, portfolio_id)
