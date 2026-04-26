"""create defects nozzles and algorithm steps tables

Revision ID: 20260426_0002
Revises: 20260426_0001
Create Date: 2026-04-26 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260426_0002"
down_revision: Union[str, None] = "20260426_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "defects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("gas_branch", sa.String(length=255), nullable=False),
        sa.Column("is_critical", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "nozzles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("diameter_mm", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("diameter_mm"),
    )

    op.create_table(
        "algorithm_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parameter_code", sa.String(length=255), nullable=False),
        sa.Column("severity_level", sa.String(length=255), nullable=False),
        sa.Column("step_value", sa.Float(), nullable=False),
        sa.Column("step_unit", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parameter_code", "severity_level"),
    )


def downgrade() -> None:
    op.drop_table("algorithm_steps")
    op.drop_table("nozzles")
    op.drop_table("defects")
