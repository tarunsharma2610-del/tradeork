from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    model = Portfolio

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_by_user(self, user_id: UUID) -> list[Portfolio]:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_for_user(
        self, user_id: UUID, portfolio_id: UUID
    ) -> Portfolio | None:
        stmt = select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == user_id
        )
        return self.db.scalars(stmt).first()

    def get_by_name(self, user_id: UUID, name: str) -> Portfolio | None:
        stmt = select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.name == name,
        )
        return self.db.scalars(stmt).first()

    def create(
        self,
        *,
        user_id: UUID,
        name: str,
        description: str | None,
        initial_capital: Decimal,
        currency: str,
    ) -> Portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            initial_capital=initial_capital,
            currency=currency,
        )
        self.db.add(portfolio)
        self.db.flush()
        self.db.refresh(portfolio)
        return portfolio
