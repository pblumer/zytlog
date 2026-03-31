"""add working weekday patterns and employee weekday overrides

Revision ID: 20260331_0002
Revises: 20260330_0001
Create Date: 2026-03-31 00:00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0002"
down_revision: str | None = "20260330_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "working_time_models",
        sa.Column("default_workdays_per_week", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_monday", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_tuesday", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_wednesday", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_thursday", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_friday", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_saturday", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workday_sunday", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.execute("UPDATE working_time_models SET default_workdays_per_week = workdays_per_week")

    op.drop_column("working_time_models", "workdays_per_week")

    op.add_column("employees", sa.Column("workday_monday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_tuesday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_wednesday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_thursday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_friday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_saturday", sa.Boolean(), nullable=True))
    op.add_column("employees", sa.Column("workday_sunday", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "workday_sunday")
    op.drop_column("employees", "workday_saturday")
    op.drop_column("employees", "workday_friday")
    op.drop_column("employees", "workday_thursday")
    op.drop_column("employees", "workday_wednesday")
    op.drop_column("employees", "workday_tuesday")
    op.drop_column("employees", "workday_monday")

    op.add_column(
        "working_time_models",
        sa.Column("workdays_per_week", sa.Integer(), nullable=False, server_default="5"),
    )
    op.execute("UPDATE working_time_models SET workdays_per_week = default_workdays_per_week")

    op.drop_column("working_time_models", "default_workday_sunday")
    op.drop_column("working_time_models", "default_workday_saturday")
    op.drop_column("working_time_models", "default_workday_friday")
    op.drop_column("working_time_models", "default_workday_thursday")
    op.drop_column("working_time_models", "default_workday_wednesday")
    op.drop_column("working_time_models", "default_workday_tuesday")
    op.drop_column("working_time_models", "default_workday_monday")
    op.drop_column("working_time_models", "default_workdays_per_week")
