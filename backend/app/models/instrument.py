import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint(
            "exchange",
            "symbol",
            "instrument_type",
            "expiry",
            "strike_price",
            "option_type",
            name="uq_instruments_natural_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True
    )
    instrument_type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )
    segment: Mapped[str | None] = mapped_column(String(32))
    expiry: Mapped[date | None] = mapped_column(Date)
    strike_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    option_type: Mapped[str | None] = mapped_column(String(4))
    lot_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tick_size: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0.05"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False, index=True
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

    def __repr__(self) -> str:
        return f"<Instrument id={self.id} symbol={self.symbol} exchange={self.exchange}>"
