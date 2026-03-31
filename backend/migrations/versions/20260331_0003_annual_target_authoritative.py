"""make annual target hours the single source of truth

Revision ID: 20260331_0003
Revises: 20260331_0002
Create Date: 2026-03-31 00:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0003"
down_revision: str | None = "20260331_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fallback migration strategy:
    # - if annual_target_hours is still NULL for old records, derive it from weekly_target_hours * 52
    # - then enforce annual_target_hours as required and drop legacy weekly/default_workdays fields
    op.execute(
        """
        UPDATE working_time_models
        SET annual_target_hours = weekly_target_hours * 52
        WHERE annual_target_hours IS NULL
        """
    )

    op.alter_column("working_time_models", "annual_target_hours", existing_type=sa.Numeric(7, 2), nullable=False)
    op.drop_column("working_time_models", "default_workdays_per_week")
    op.drop_column("working_time_models", "weekly_target_hours")


def downgrade() -> None:
    op.add_column(
        "working_time_models",
        sa.Column("weekly_target_hours", sa.Numeric(precision=5, scale=2), nullable=False, server_default="40"),
    )
    op.add_column(
        "working_time_models",
        sa.Column("default_workdays_per_week", sa.Integer(), nullable=False, server_default="5"),
    )

    # Approximation for backward compatibility: derive weekly target from annual target.
    op.execute(
        """
        UPDATE working_time_models
        SET weekly_target_hours = ROUND(annual_target_hours / 52.0, 2)
        """
    )
    op.execute(
        """
        UPDATE working_time_models
        SET default_workdays_per_week =
            CAST(default_workday_monday AS INTEGER) +
            CAST(default_workday_tuesday AS INTEGER) +
            CAST(default_workday_wednesday AS INTEGER) +
            CAST(default_workday_thursday AS INTEGER) +
            CAST(default_workday_friday AS INTEGER) +
            CAST(default_workday_saturday AS INTEGER) +
            CAST(default_workday_sunday AS INTEGER)
        """
    )

    op.alter_column("working_time_models", "annual_target_hours", existing_type=sa.Numeric(7, 2), nullable=True)
