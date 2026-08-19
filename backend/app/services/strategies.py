from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.strategies import StrategyRepository
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.portfolios import PortfolioService


class StrategyService:
    """Strategy CRUD, always scoped to a portfolio the caller owns.

    Ownership is enforced by resolving the portfolio through
    ``PortfolioService.get`` (404 for other tenants), then every strategy
    lookup is additionally constrained to that portfolio id.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = StrategyRepository(db)

    def _portfolio(self, user_id: UUID, portfolio_id: UUID):
        return PortfolioService(self.db).get(user_id, portfolio_id)

    def list(
        self, user_id: UUID, portfolio_id: UUID, status: str | None = None
    ):
        self._portfolio(user_id, portfolio_id)
        return self.repo.list_for_portfolio(portfolio_id, status)

    def get(self, user_id: UUID, portfolio_id: UUID, strategy_id: UUID):
        self._portfolio(user_id, portfolio_id)
        strategy = self.repo.get_for_portfolio(portfolio_id, strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found.",
            )
        return strategy

    def create(self, user_id: UUID, portfolio_id: UUID, data: StrategyCreate):
        self._portfolio(user_id, portfolio_id)
        if self.repo.get_by_name(portfolio_id, data.name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A strategy named '{data.name}' already exists in "
                    "this portfolio."
                ),
            )
        strategy = self.repo.create(
            user_id=user_id,
            portfolio_id=portfolio_id,
            name=data.name,
            description=data.description,
            strategy_type=data.strategy_type.value,
            parameters=data.parameters,
            status=data.status.value,
        )
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def update(
        self,
        user_id: UUID,
        portfolio_id: UUID,
        strategy_id: UUID,
        data: StrategyUpdate,
    ):
        strategy = self.get(user_id, portfolio_id, strategy_id)
        if data.name is not None and data.name != strategy.name:
            existing = self.repo.get_by_name(portfolio_id, data.name)
            if existing is not None and existing.id != strategy.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"A strategy named '{data.name}' already exists in "
                        "this portfolio."
                    ),
                )
            strategy.name = data.name
        if data.description is not None:
            strategy.description = data.description
        if data.strategy_type is not None:
            strategy.strategy_type = data.strategy_type.value
        if data.parameters is not None:
            strategy.parameters = data.parameters
        if data.status is not None:
            strategy.status = data.status.value
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def delete(self, user_id: UUID, portfolio_id: UUID, strategy_id: UUID) -> None:
        strategy = self.get(user_id, portfolio_id, strategy_id)
        self.db.delete(strategy)
        self.db.commit()
