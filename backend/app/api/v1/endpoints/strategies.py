from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyRead, StrategyUpdate
from app.services.strategies import StrategyService

router = APIRouter(
    prefix="/portfolios/{portfolio_id}/strategies", tags=["strategies"]
)


@router.get("", response_model=list[StrategyRead])
async def list_strategies(
    portfolio_id: UUID,
    strategy_status: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return StrategyService(db).list(current_user.id, portfolio_id, strategy_status)


@router.post(
    "", response_model=StrategyRead, status_code=status.HTTP_201_CREATED
)
async def create_strategy(
    portfolio_id: UUID,
    data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StrategyRead:
    return StrategyService(db).create(current_user.id, portfolio_id, data)


@router.get("/{strategy_id}", response_model=StrategyRead)
async def get_strategy(
    portfolio_id: UUID,
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StrategyRead:
    return StrategyService(db).get(current_user.id, portfolio_id, strategy_id)


@router.patch("/{strategy_id}", response_model=StrategyRead)
async def update_strategy(
    portfolio_id: UUID,
    strategy_id: UUID,
    data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StrategyRead:
    return StrategyService(db).update(
        current_user.id, portfolio_id, strategy_id, data
    )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    portfolio_id: UUID,
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    StrategyService(db).delete(current_user.id, portfolio_id, strategy_id)
