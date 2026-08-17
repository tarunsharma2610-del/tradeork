from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import Position
from app.repositories.base import BaseRepository


class PositionRepository(BaseRepository[Position]):
    model = Position

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_portfolio(self, portfolio_id: UUID) -> list[Position]:
        stmt = (
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(Position.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_for_portfolio_instrument(
        self, portfolio_id: UUID, instrument_id: UUID
    ) -> Position | None:
        stmt = select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.instrument_id == instrument_id,
        )
        return self.db.scalars(stmt).first()
