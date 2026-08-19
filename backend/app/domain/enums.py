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


class ExecutionMode(StrEnum):
    """How a portfolio's orders are executed.

    PAPER — simulated by the paper engine (always safe, default).
    LIVE  — routed to a real broker through a ``BrokerAdapter``; the paper
            ledger stays the source of truth for the user's displayed book.
    """

    PAPER = "paper"
    LIVE = "live"


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


class StrategyType(StrEnum):
    """Kind of strategy. ``manual`` covers user-defined rules entered directly
    in the UI; the named types map to the built-in engines planned in the
    roadmap (Phase 7) and are stored now so strategies stay forward-compatible.
    """

    MANUAL = "manual"
    RSI = "rsi"
    EMA_CROSSOVER = "ema_crossover"
    VWAP = "vwap"
    SUPERTREND = "supertrend"
    BREAKOUT = "breakout"
    CUSTOM = "custom"


class StrategyStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
