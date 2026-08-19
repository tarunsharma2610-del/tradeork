import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class BrokerConnection(Base):
    """A user's broker account credentials (per-user live execution token).

    This is the "add your Upstox API" store surfaced in Settings. Live
    portfolios resolve their broker adapter from the user's connection here
    (via :func:`app.services.broker_factory.get_broker_for_user`) so each user
    executes through their own broker account instead of a single
    server-configured token.

    Secrets (``access_token``, ``api_key``) are stored encrypted at rest with
    Fernet keyed off ``SECRET_KEY`` — never plaintext, and never returned by
    any API (only a masked preview like ``****abcd``).
    """

    __tablename__ = "broker_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Broker provider, e.g. "upstox". Validated in the schema/service layer.
    provider: Mapped[str] = mapped_column(
        String(20), default="upstox", nullable=False, server_default="upstox"
    )
    label: Mapped[str | None] = mapped_column(String(100))
    access_token_encrypted: Mapped[str] = mapped_column(String(1000), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
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

    def __repr__(self) -> str:
        return (
            f"<BrokerConnection id={self.id} provider={self.provider} "
            f"user_id={self.user_id}>"
        )
