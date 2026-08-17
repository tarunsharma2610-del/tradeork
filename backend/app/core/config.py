from datetime import timedelta
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Tradeork"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+psycopg://tradeork:tradeork@db:5432/tradeork"
    )
    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    RATE_LIMIT_ENABLED: bool = True

    # Market data provider selection.
    # "mock"  -> synthetic quotes, always labelled is_mock=true
    # "upstox" -> live Upstox v2 REST quotes (requires credentials below)
    MARKET_DATA_PROVIDER: str = "mock"
    MARKET_DATA_POLL_INTERVAL: float = 2.0

    # Paper trading engine.
    # Background loop that fills pending LIMIT orders once they become
    # marketable. Disabled in tests; the loop runs inside the app lifespan.
    PAPER_MATCHER_ENABLED: bool = True
    PAPER_MATCHER_INTERVAL: float = 5.0

    # Broker execution adapter (LIVE side of PAPER/LIVE separation).
    # "mock"   -> in-process simulator, is_mock=true (default)
    # "upstox" -> live Upstox v2 order placement (requires credentials below)
    # The paper engine never calls a broker; this seam is for a future live
    # execution mode and is currently exercised through tests only.
    BROKER_ADAPTER: str = "mock"
    UPSTOX_BROKER_PRODUCT: str = "D"

    # Upstox v2 API (live provider + broker). Tokens are long-lived app access
    # tokens; OAuth refresh flow is out of scope for now.
    UPSTOX_API_KEY: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""
    UPSTOX_BASE_URL: str = "https://api.upstox.com/v2"

    @field_validator("MARKET_DATA_PROVIDER")
    @classmethod
    def _validate_market_data_provider(cls, v: str) -> str:
        provider = v.lower()
        if provider not in ("mock", "upstox"):
            raise ValueError("MARKET_DATA_PROVIDER must be 'mock' or 'upstox'")
        return provider

    @field_validator("BROKER_ADAPTER")
    @classmethod
    def _validate_broker_adapter(cls, v: str) -> str:
        adapter = v.lower()
        if adapter not in ("mock", "upstox"):
            raise ValueError("BROKER_ADAPTER must be 'mock' or 'upstox'")
        return adapter

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def _enforce_secret_in_production(cls, v: str, info: Any) -> str:
        if info.data.get("ENVIRONMENT") == "production":
            if v == "change-me-in-production":
                raise ValueError(
                    "SECRET_KEY must be replaced with a strong random value in production"
                )
            if len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters long in production"
                )
        return v

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
