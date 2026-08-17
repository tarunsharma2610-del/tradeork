from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import OrderSide


class PositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    instrument_id: UUID
    symbol: str
    exchange: str
    quantity: int
    avg_price: Decimal
    realized_pnl: Decimal
    last_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    updated_at: datetime


class PortfolioSummary(BaseModel):
    portfolio_id: UUID
    name: str
    initial_capital: Decimal
    cash: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    equity: Decimal
    positions_count: int
    open_orders_count: int


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    instrument_id: UUID
    symbol: str
    exchange: str
    side: OrderSide
    quantity: int
    price: Decimal
    realized_pnl: Decimal
    executed_at: datetime
