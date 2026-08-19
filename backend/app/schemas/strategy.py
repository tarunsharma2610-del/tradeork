from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import StrategyStatus, StrategyType


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    strategy_type: StrategyType = StrategyType.MANUAL
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: StrategyStatus = StrategyStatus.ACTIVE


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    strategy_type: StrategyType | None = None
    parameters: dict[str, Any] | None = None
    status: StrategyStatus | None = None


class StrategyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    portfolio_id: UUID
    name: str
    description: str | None
    strategy_type: StrategyType
    parameters: dict[str, Any]
    status: StrategyStatus
    created_at: datetime
    updated_at: datetime
