from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_portfolio(
        self, portfolio_id: UUID, status: str | None = None, limit: int = 100
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.portfolio_id == portfolio_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Order.status == status)
        return list(self.db.scalars(stmt).all())

    def get_for_portfolio(
        self, portfolio_id: UUID, order_id: UUID
    ) -> Order | None:
        stmt = select(Order).where(
            Order.id == order_id, Order.portfolio_id == portfolio_id
        )
        return self.db.scalars(stmt).first()

    def list_pending(self) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.status == "pending")
            .order_by(Order.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())
