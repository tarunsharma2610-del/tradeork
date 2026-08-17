from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExecutionMode, PortfolioStatus


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    initial_capital: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    execution_mode: ExecutionMode = ExecutionMode.PAPER


class PortfolioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    initial_capital: Decimal | None = Field(
        default=None, gt=0, max_digits=18, decimal_places=2
    )
    status: PortfolioStatus | None = None
    execution_mode: ExecutionMode | None = None


class PortfolioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    initial_capital: Decimal
    cash: Decimal
    currency: str
    status: PortfolioStatus
    execution_mode: ExecutionMode
    created_at: datetime
    updated_at: datetime
