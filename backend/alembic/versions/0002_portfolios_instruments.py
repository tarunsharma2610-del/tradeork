"""add portfolios and instruments

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("initial_capital", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_portfolios_user_name"),
    )
    op.create_index(
        op.f("ix_portfolios_user_id"), "portfolios", ["user_id"], unique=False
    )

    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("instrument_type", sa.String(length=16), nullable=False),
        sa.Column("segment", sa.String(length=32), nullable=True),
        sa.Column("expiry", sa.Date(), nullable=True),
        sa.Column("strike_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("option_type", sa.String(length=4), nullable=True),
        sa.Column("lot_size", sa.Integer(), nullable=False),
        sa.Column("tick_size", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exchange",
            "symbol",
            "instrument_type",
            "expiry",
            "strike_price",
            "option_type",
            name="uq_instruments_natural_key",
        ),
    )
    op.create_index(
        op.f("ix_instruments_exchange"),
        "instruments",
        ["exchange"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instruments_instrument_type"),
        "instruments",
        ["instrument_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instruments_is_active"),
        "instruments",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_instruments_is_active"), table_name="instruments")
    op.drop_index(
        op.f("ix_instruments_instrument_type"), table_name="instruments"
    )
    op.drop_index(op.f("ix_instruments_exchange"), table_name="instruments")
    op.drop_table("instruments")
    op.drop_index(op.f("ix_portfolios_user_id"), table_name="portfolios")
    op.drop_table("portfolios")
