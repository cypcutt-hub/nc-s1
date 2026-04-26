"""add recommendation rules table

Revision ID: 20260426_0004
Revises: 20260426_0003
Create Date: 2026-04-26 00:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260426_0004"
down_revision: Union[str, None] = "20260426_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("defect_code", sa.String(length=255), nullable=False),
        sa.Column("parameter", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("base_delta", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )

    recommendation_rules_table = sa.table(
        "recommendation_rules",
        sa.column("defect_code", sa.String),
        sa.column("parameter", sa.String),
        sa.column("direction", sa.String),
        sa.column("base_delta", sa.Float),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        recommendation_rules_table,
        [
            {
                "defect_code": "no_cut",
                "parameter": "power",
                "direction": "increase",
                "base_delta": 0.05,
                "is_active": True,
            },
            {
                "defect_code": "no_cut",
                "parameter": "speed",
                "direction": "decrease",
                "base_delta": 0.05,
                "is_active": True,
            },
            {
                "defect_code": "burr",
                "parameter": "power",
                "direction": "decrease",
                "base_delta": 0.05,
                "is_active": True,
            },
            {
                "defect_code": "burr",
                "parameter": "speed",
                "direction": "increase",
                "base_delta": 0.05,
                "is_active": True,
            },
            {
                "defect_code": "overburn",
                "parameter": "power",
                "direction": "decrease",
                "base_delta": 0.10,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("recommendation_rules")
