"""Shared domain vocabulary used across the trading engine.

These enums are the single source of truth for market and instrument types.
Order, position and execution models in later phases must reuse these
definitions so that manual trading, strategies, backtesting and live trading
share identical semantics.
"""

from enum import StrEnum


class Exchange(StrEnum):
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"


class InstrumentType(StrEnum):
    EQUITY = "EQUITY"
    FUTURE = "FUTURE"
    OPTION = "OPTION"


class OptionType(StrEnum):
    CE = "CE"
    PE = "PE"


class PortfolioStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
