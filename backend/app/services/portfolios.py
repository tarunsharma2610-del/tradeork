from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.repositories.portfolios import PortfolioRepository
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


class PortfolioService:
    """Portfolio operations, always scoped to the owning user.

    Ownership is enforced here (never trusted from the request body), so a
    user can only ever see or mutate their own portfolios.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PortfolioRepository(db)

    def create(self, user_id: UUID, data: PortfolioCreate) -> Portfolio:
        if self.repo.get_by_name(user_id, data.name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A portfolio named '{data.name}' already exists.",
            )
        portfolio = self.repo.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
            initial_capital=data.initial_capital,
            currency=data.currency,
        )
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def list(self, user_id: UUID) -> list[Portfolio]:
        return self.repo.list_by_user(user_id)

    def get(self, user_id: UUID, portfolio_id: UUID) -> Portfolio:
        portfolio = self.repo.get_for_user(user_id, portfolio_id)
        if portfolio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found.",
            )
        return portfolio

    def update(
        self, user_id: UUID, portfolio_id: UUID, data: PortfolioUpdate
    ) -> Portfolio:
        portfolio = self.get(user_id, portfolio_id)
        if data.name is not None and data.name != portfolio.name:
            if self.repo.get_by_name(user_id, data.name) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A portfolio named '{data.name}' already exists.",
                )
            portfolio.name = data.name
        if data.description is not None:
            portfolio.description = data.description
        if data.initial_capital is not None:
            portfolio.initial_capital = data.initial_capital
        if data.status is not None:
            portfolio.status = data.status.value
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def delete(self, user_id: UUID, portfolio_id: UUID) -> None:
        portfolio = self.get(user_id, portfolio_id)
        self.db.delete(portfolio)
        self.db.commit()
