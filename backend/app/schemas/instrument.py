from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import Exchange, InstrumentType, OptionType


class InstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    symbol: str
    name: str
    exchange: Exchange
    instrument_type: InstrumentType
    segment: str | None
    expiry: date | None
    strike_price: Decimal | None
    option_type: OptionType | None
    lot_size: int
    tick_size: Decimal
    is_active: bool
    created_at: datetime
