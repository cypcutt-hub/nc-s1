"""add sessions and iterations tables

Revision ID: 20260426_0003
Revises: 20260426_0002
Create Date: 2026-04-26 00:25:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260426_0003"
down_revision: Union[str, None] = "20260426_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cut_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_name", sa.String(length=255), nullable=False),
        sa.Column("material_group", sa.String(length=255), nullable=False),
        sa.Column("thickness_mm", sa.Float(), nullable=False),
        sa.Column("gas_branch", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "cut_iterations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("defect_code", sa.String(length=255), nullable=False),
        sa.Column("severity_level", sa.Integer(), nullable=False),
        sa.Column("power_before", sa.Float(), nullable=False),
        sa.Column("speed_before", sa.Float(), nullable=False),
        sa.Column("focus_before", sa.Float(), nullable=False),
        sa.Column("pressure_before", sa.Float(), nullable=False),
        sa.Column("power_after", sa.Float(), nullable=False),
        sa.Column("speed_after", sa.Float(), nullable=False),
        sa.Column("focus_after", sa.Float(), nullable=False),
        sa.Column("pressure_after", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["defect_code"], ["defects.code"]),
        sa.ForeignKeyConstraint(["session_id"], ["cut_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("cut_iterations")
    op.drop_table("cut_sessions")
