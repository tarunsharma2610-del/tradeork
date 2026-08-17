from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import Exchange


class Quote(BaseModel):
    """A single instrument quote.

    `is_mock` is always surfaced to the consumer so that simulated data can
    never be mistaken for real market data.
    """

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    exchange: Exchange
    last_price: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    prev_close: Decimal
    volume: int
    quote_time: datetime
    is_mock: bool
    source: str
