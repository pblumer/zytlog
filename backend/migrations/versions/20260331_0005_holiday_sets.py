"""refactor holidays to reusable holiday sets

Revision ID: 20260331_0005
Revises: 20260331_0004
Create Date: 2026-03-31 09:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0005"
down_revision: str | None = "20260331_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "holiday_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("region_code", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_holiday_sets_tenant_id", "holiday_sets", ["tenant_id"])

    op.add_column("holidays", sa.Column("holiday_set_id", sa.Integer(), nullable=True))
    op.create_index("ix_holidays_holiday_set_id", "holidays", ["holiday_set_id"])
    op.create_foreign_key("fk_holidays_holiday_set_id", "holidays", "holiday_sets", ["holiday_set_id"], ["id"])

    op.add_column("tenants", sa.Column("default_holiday_set_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tenants_default_holiday_set_id",
        "tenants",
        "holiday_sets",
        ["default_holiday_set_id"],
        ["id"],
    )

    op.add_column("employees", sa.Column("holiday_set_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_employees_holiday_set_id",
        "employees",
        "holiday_sets",
        ["holiday_set_id"],
        ["id"],
    )

    bind = op.get_bind()
    tenant_ids = [row[0] for row in bind.execute(sa.text("SELECT DISTINCT tenant_id FROM holidays")).all()]
    for tenant_id in tenant_ids:
        inserted = bind.execute(
            sa.text(
                """
                INSERT INTO holiday_sets
                    (tenant_id, name, description, source, active, created_at, updated_at)
                VALUES
                    (:tenant_id, 'Standard', 'Automatisch migrierter Standard-Feiertagssatz', 'manual', true, now(), now())
                RETURNING id
                """
            ),
            {"tenant_id": tenant_id},
        ).scalar_one()
        bind.execute(
            sa.text("UPDATE holidays SET holiday_set_id = :holiday_set_id WHERE tenant_id = :tenant_id"),
            {"holiday_set_id": inserted, "tenant_id": tenant_id},
        )
        bind.execute(
            sa.text("UPDATE tenants SET default_holiday_set_id = :holiday_set_id WHERE id = :tenant_id"),
            {"holiday_set_id": inserted, "tenant_id": tenant_id},
        )

    op.alter_column("holidays", "holiday_set_id", nullable=False)
    op.drop_constraint("uq_holidays_tenant_date", "holidays", type_="unique")
    op.create_unique_constraint("uq_holidays_holiday_set_date", "holidays", ["holiday_set_id", "date"])


def downgrade() -> None:
    op.drop_constraint("uq_holidays_holiday_set_date", "holidays", type_="unique")
    op.create_unique_constraint("uq_holidays_tenant_date", "holidays", ["tenant_id", "date"])
    op.drop_constraint("fk_holidays_holiday_set_id", "holidays", type_="foreignkey")
    op.drop_index("ix_holidays_holiday_set_id", table_name="holidays")
    op.drop_column("holidays", "holiday_set_id")

    op.drop_constraint("fk_employees_holiday_set_id", "employees", type_="foreignkey")
    op.drop_column("employees", "holiday_set_id")

    op.drop_constraint("fk_tenants_default_holiday_set_id", "tenants", type_="foreignkey")
    op.drop_column("tenants", "default_holiday_set_id")

    op.drop_index("ix_holiday_sets_tenant_id", table_name="holiday_sets")
    op.drop_table("holiday_sets")
