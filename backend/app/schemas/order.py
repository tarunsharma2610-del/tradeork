from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import ExecutionMode, OrderSide, OrderStatus, OrderType


class OrderCreate(BaseModel):
    instrument_id: UUID
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(gt=0, le=1000000)
    limit_price: Decimal | None = Field(
        default=None, gt=0, max_digits=18, decimal_places=2
    )

    @model_validator(mode="after")
    def _limit_price_required_for_limit(self) -> "OrderCreate":
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for LIMIT orders.")
        if self.order_type == OrderType.MARKET and self.limit_price is not None:
            raise ValueError("limit_price must be omitted for MARKET orders.")
        return self


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    instrument_id: UUID
    symbol: str
    exchange: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Decimal | None
    execution_mode: ExecutionMode
    broker_order_id: str | None
    status: OrderStatus
    filled_quantity: int
    avg_fill_price: Decimal | None
    filled_at: datetime | None
    reject_reason: str | None
    created_at: datetime
