from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.repositories.base import BaseRepository


class InstrumentRepository(BaseRepository[Instrument]):
    model = Instrument

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def search(
        self,
        *,
        query: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        limit: int = 50,
    ) -> list[Instrument]:
        stmt = select(Instrument).where(Instrument.is_active.is_(True))
        if query:
            like = f"%{query.upper()}%"
            stmt = stmt.where(
                or_(
                    Instrument.symbol.ilike(like),
                    Instrument.name.ilike(like),
                )
            )
        if exchange:
            stmt = stmt.where(Instrument.exchange == exchange)
        if instrument_type:
            stmt = stmt.where(Instrument.instrument_type == instrument_type)
        stmt = stmt.order_by(Instrument.symbol).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_natural_key(
        self,
        exchange: str,
        symbol: str,
        instrument_type: str,
        expiry: date | None,
        strike_price: Decimal | None,
        option_type: str | None,
    ) -> Instrument | None:
        stmt = select(Instrument).where(
            Instrument.exchange == exchange,
            Instrument.symbol == symbol,
            Instrument.instrument_type == instrument_type,
            Instrument.expiry == expiry,
            Instrument.strike_price == strike_price,
            Instrument.option_type == option_type,
        )
        return self.db.scalars(stmt).first()

    def get_by_exchange_symbol(
        self, exchange: str, symbol: str
    ) -> Instrument | None:
        stmt = select(Instrument).where(
            Instrument.exchange == exchange,
            Instrument.symbol == symbol,
        )
        return self.db.scalars(stmt).first()
