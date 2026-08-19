from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import BrokerProvider


class BrokerConnectionCreate(BaseModel):
    provider: BrokerProvider = BrokerProvider.UPSTOX
    label: str | None = Field(default=None, max_length=100)
    access_token: str = Field(min_length=10, max_length=1000)
    api_key: str | None = Field(default=None, max_length=1000)


class BrokerConnectionUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=100)
    access_token: str | None = Field(default=None, min_length=10, max_length=1000)
    api_key: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


def mask_secret(secret: str) -> str:
    """Render a masked preview of a secret, e.g. ``****efgh``.

    Only the last 4 characters are shown; shorter values are fully masked.
    """
    if len(secret) <= 4:
        return "****"
    return f"****{secret[-4:]}"


class BrokerConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: BrokerProvider
    label: str | None
    access_token_masked: str
    api_key_masked: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
