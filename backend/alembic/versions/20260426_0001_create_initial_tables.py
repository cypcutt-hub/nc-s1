"""create initial neurocut tables

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260426_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("material_group", sa.String(length=255), nullable=False),
        sa.Column("default_gas_branch", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("laser_power_w", sa.Integer(), nullable=False),
        sa.Column("lens_focal_length_mm", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "base_modes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.Integer(), nullable=True),
        sa.Column("thickness_mm", sa.Float(), nullable=False),
        sa.Column("gas_type", sa.String(), nullable=False),
        sa.Column("power_percent", sa.Float(), nullable=False),
        sa.Column("speed_m_min", sa.Float(), nullable=False),
        sa.Column("frequency_hz", sa.Float(), nullable=True),
        sa.Column("pressure_bar", sa.Float(), nullable=False),
        sa.Column("focus_mm", sa.Float(), nullable=False),
        sa.Column("cutting_height_mm", sa.Float(), nullable=False),
        sa.Column("duty_cycle_percent", sa.Float(), nullable=True),
        sa.Column("nozzle_diameter_mm", sa.Float(), nullable=False),
        sa.Column("trust_level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"]),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("base_modes")
    op.drop_table("machines")
    op.drop_table("materials")
