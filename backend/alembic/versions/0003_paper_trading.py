"""add paper trading: orders, positions, trades, portfolios.cash

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column(
            "cash",
            sa.Numeric(precision=18, scale=2),
            server_default="0",
            nullable=False,
        ),
    )
    op.execute("UPDATE portfolios SET cash = initial_capital")
    if op.get_context().dialect.name != "sqlite":
        op.alter_column("portfolios", "cash", server_default=None)

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("order_type", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("filled_quantity", sa.Integer(), nullable=False),
        sa.Column("avg_fill_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_orders_portfolio_id"), "orders", ["portfolio_id"], unique=False
    )
    op.create_index(
        op.f("ix_orders_instrument_id"), "orders", ["instrument_id"], unique=False
    )
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)

    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("avg_price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "portfolio_id",
            "instrument_id",
            name="uq_positions_portfolio_instrument",
        ),
    )
    op.create_index(
        op.f("ix_positions_user_id"), "positions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_positions_portfolio_id"), "positions", ["portfolio_id"], unique=False
    )
    op.create_index(
        op.f("ix_positions_instrument_id"), "positions", ["instrument_id"], unique=False
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_user_id"), "trades", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_trades_portfolio_id"), "trades", ["portfolio_id"], unique=False
    )
    op.create_index(op.f("ix_trades_order_id"), "trades", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_trades_instrument_id"), "trades", ["instrument_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trades_instrument_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_order_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_portfolio_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_user_id"), table_name="trades")
    op.drop_table("trades")
    op.drop_index(op.f("ix_positions_instrument_id"), table_name="positions")
    op.drop_index(op.f("ix_positions_portfolio_id"), table_name="positions")
    op.drop_index(op.f("ix_positions_user_id"), table_name="positions")
    op.drop_table("positions")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_instrument_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_portfolio_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_column("portfolios", "cash")
