"""add strategies: per-portfolio strategy definitions

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "strategy_type",
            sa.String(length=20),
            server_default="manual",
            nullable=False,
        ),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), server_default="active", nullable=False
        ),
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
        sa.ForeignKeyConstraint(
            ["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "portfolio_id", "name", name="uq_strategies_portfolio_name"
        ),
    )
    op.create_index(
        op.f("ix_strategies_user_id"), "strategies", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_strategies_portfolio_id"),
        "strategies",
        ["portfolio_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_strategies_portfolio_id"), table_name="strategies")
    op.drop_index(op.f("ix_strategies_user_id"), table_name="strategies")
    op.drop_table("strategies")
