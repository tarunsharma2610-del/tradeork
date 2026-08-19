import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.user import User


class Strategy(Base):
    """A user-defined trading strategy, scoped to a single portfolio.

    Strategies are reference/configuration data for now — they are stored and
    editable per portfolio but do not yet generate orders. The roadmap
    (Phase 7/8) wires them into a signal engine + AutoTrade; keeping
    ``parameters`` as free-form JSON lets those engines read per-strategy
    configuration without a schema churn later.
    """

    __tablename__ = "strategies"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "name", name="uq_strategies_portfolio_name"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    strategy_type: Mapped[str] = mapped_column(
        String(20), default="manual", nullable=False, server_default="manual"
    )
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship()
    portfolio: Mapped["Portfolio"] = relationship()

    def __repr__(self) -> str:
        return f"<Strategy id={self.id} name={self.name} type={self.strategy_type}>"
