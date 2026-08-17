from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.repositories.base import BaseRepository


class TradeRepository(BaseRepository[Trade]):
    model = Trade

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_portfolio(
        self, portfolio_id: UUID, limit: int = 100
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .where(Trade.portfolio_id == portfolio_id)
            .order_by(Trade.executed_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
