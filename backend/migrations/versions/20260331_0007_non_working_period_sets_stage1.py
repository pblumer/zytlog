"""add non working period sets stage1

Revision ID: 20260331_0007
Revises: 20260331_0006
Create Date: 2026-03-31 17:00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0007"
down_revision: str | None = "20260331_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "non_working_period_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_non_working_period_sets_tenant_id", "non_working_period_sets", ["tenant_id"])

    op.create_table(
        "non_working_periods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("non_working_period_set_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["non_working_period_set_id"], ["non_working_period_sets.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "non_working_period_set_id",
            "name",
            "start_date",
            "end_date",
            name="uq_non_working_periods_set_named_range",
        ),
    )
    op.create_index("ix_non_working_periods_tenant_id", "non_working_periods", ["tenant_id"])
    op.create_index(
        "ix_non_working_periods_non_working_period_set_id",
        "non_working_periods",
        ["non_working_period_set_id"],
    )

    op.add_column("employees", sa.Column("non_working_period_set_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_employees_non_working_period_set_id",
        "employees",
        "non_working_period_sets",
        ["non_working_period_set_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_employees_non_working_period_set_id", "employees", type_="foreignkey")
    op.drop_column("employees", "non_working_period_set_id")

    op.drop_index("ix_non_working_periods_non_working_period_set_id", table_name="non_working_periods")
    op.drop_index("ix_non_working_periods_tenant_id", table_name="non_working_periods")
    op.drop_table("non_working_periods")

    op.drop_index("ix_non_working_period_sets_tenant_id", table_name="non_working_period_sets")
    op.drop_table("non_working_period_sets")
