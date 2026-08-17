"""add live execution mode: portfolios.execution_mode, orders.execution_mode + broker_order_id

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column(
            "execution_mode",
            sa.String(length=8),
            server_default="paper",
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "execution_mode",
            sa.String(length=8),
            server_default="paper",
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column("broker_order_id", sa.String(length=64), nullable=True),
    )
    if op.get_context().dialect.name != "sqlite":
        op.alter_column("portfolios", "execution_mode", server_default=None)
        op.alter_column("orders", "execution_mode", server_default=None)


def downgrade() -> None:
    op.drop_column("orders", "broker_order_id")
    op.drop_column("orders", "execution_mode")
    op.drop_column("portfolios", "execution_mode")
