from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.schemas.position import PortfolioSummary, PositionRead
from app.services.paper_engine import PaperOrderEngine

router = APIRouter(prefix="/portfolios/{portfolio_id}", tags=["trading"])


def _engine(db: Session) -> PaperOrderEngine:
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
    return await _engine(db).place_order(current_user.id, portfolio_id, data)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    portfolio_id: UUID,
    order_status: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return _engine(db).list_orders(current_user.id, portfolio_id, order_status)


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
    return _engine(db).cancel_order(current_user.id, portfolio_id, order_id)


@router.get("/positions", response_model=list[PositionRead])
async def list_positions(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return await _engine(db).list_positions(current_user.id, portfolio_id)


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary(
    portfolio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return await _engine(db).portfolio_summary(current_user.id, portfolio_id)
