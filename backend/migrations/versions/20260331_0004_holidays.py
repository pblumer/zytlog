"""add tenant-scoped public holidays

Revision ID: 20260331_0004
Revises: 20260331_0003
Create Date: 2026-03-31 01:15:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0004"
down_revision: str | None = "20260331_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "date", name="uq_holidays_tenant_date"),
    )
    op.create_index("ix_holidays_tenant_id", "holidays", ["tenant_id"])
    op.create_index("ix_holidays_date", "holidays", ["date"])


def downgrade() -> None:
    op.drop_index("ix_holidays_date", table_name="holidays")
    op.drop_index("ix_holidays_tenant_id", table_name="holidays")
    op.drop_table("holidays")
