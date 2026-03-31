"""add absence stage1 domain

Revision ID: 20260331_0006
Revises: 20260331_0005
Create Date: 2026-03-31 14:00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260331_0006"
down_revision: str | None = "20260331_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


absence_type = sa.Enum("vacation", "sickness", name="absencetype")
duration_type = sa.Enum("full_day", "half_day_am", "half_day_pm", name="absencedurationtype")


def upgrade() -> None:
    absence_type.create(op.get_bind(), checkfirst=True)
    duration_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "absences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("absence_type", absence_type, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("duration_type", duration_type, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "employee_id",
            "start_date",
            "end_date",
            "absence_type",
            "duration_type",
            name="uq_absences_employee_exact",
        ),
    )
    op.create_index("ix_absences_tenant_id", "absences", ["tenant_id"])
    op.create_index("ix_absences_employee_id", "absences", ["employee_id"])
    op.create_index("ix_absences_start_date", "absences", ["start_date"])
    op.create_index("ix_absences_end_date", "absences", ["end_date"])


def downgrade() -> None:
    op.drop_index("ix_absences_end_date", table_name="absences")
    op.drop_index("ix_absences_start_date", table_name="absences")
    op.drop_index("ix_absences_employee_id", table_name="absences")
    op.drop_index("ix_absences_tenant_id", table_name="absences")
    op.drop_table("absences")

    duration_type.drop(op.get_bind(), checkfirst=True)
    absence_type.drop(op.get_bind(), checkfirst=True)
