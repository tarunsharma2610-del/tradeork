from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    model = Strategy

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_portfolio(
        self, portfolio_id: UUID, status: str | None = None
    ) -> list[Strategy]:
        stmt = (
            select(Strategy)
            .where(Strategy.portfolio_id == portfolio_id)
            .order_by(Strategy.created_at.desc())
        )
        if status:
            stmt = stmt.where(Strategy.status == status)
        return list(self.db.scalars(stmt).all())

    def get_for_portfolio(
        self, portfolio_id: UUID, strategy_id: UUID
    ) -> Strategy | None:
        stmt = select(Strategy).where(
            Strategy.id == strategy_id, Strategy.portfolio_id == portfolio_id
        )
        return self.db.scalars(stmt).first()

    def get_by_name(self, portfolio_id: UUID, name: str) -> Strategy | None:
        stmt = select(Strategy).where(
            Strategy.portfolio_id == portfolio_id, Strategy.name == name
        )
        return self.db.scalars(stmt).first()

    def create(
        self,
        *,
        user_id: UUID,
        portfolio_id: UUID,
        name: str,
        description: str | None,
        strategy_type: str,
        parameters: dict | None,
        status: str,
    ) -> Strategy:
        strategy = Strategy(
            user_id=user_id,
            portfolio_id=portfolio_id,
            name=name,
            description=description,
            strategy_type=strategy_type,
            parameters=parameters,
            status=status,
        )
        self.db.add(strategy)
        return strategy
