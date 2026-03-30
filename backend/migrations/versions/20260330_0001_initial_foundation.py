"""initial backend foundation with tenant-aware entities

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30 00:00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260330_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = sa.Enum("EMPLOYEE", "TEAM_LEAD", "ADMIN", name="userrole", create_type=False)
    tenant_type = sa.Enum("COMPANY", "DEMO", name="tenanttype", create_type=False)
    timestamp_event_type = sa.Enum("CLOCK_IN", "CLOCK_OUT", "BREAK_START", "BREAK_END", name="timestampeventtype", create_type=False)
    daily_status = sa.Enum("OPEN", "LOCKED", "CORRECTED", name="dailytimeaccountstatus", create_type=False)

    bind = op.get_bind()

    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("type", tenant_type, nullable=False, server_default="COMPANY"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("keycloak_user_id", sa.String(length=120), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="EMPLOYEE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("keycloak_user_id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    op.create_table(
        "working_time_models",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("weekly_target_hours", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("workdays_per_week", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("annual_target_hours", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_working_time_models_tenant_id"), "working_time_models", ["tenant_id"], unique=False
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("employee_number", sa.String(length=40), nullable=True),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("employment_percentage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="100"),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("working_time_model_id", sa.Integer(), nullable=True),
        sa.Column("team", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["working_time_model_id"], ["working_time_models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_employees_tenant_id"), "employees", ["tenant_id"], unique=False)

    op.create_table(
        "daily_time_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("target_minutes", sa.Integer(), nullable=False),
        sa.Column("actual_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balance_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", daily_status, nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_daily_time_accounts_employee_id"), "daily_time_accounts", ["employee_id"], unique=False
    )
    op.create_index(op.f("ix_daily_time_accounts_tenant_id"), "daily_time_accounts", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_daily_time_accounts_date"), "daily_time_accounts", ["date"], unique=False)

    op.create_table(
        "time_stamp_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", timestamp_event_type, nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="web"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_time_stamp_events_employee_id"), "time_stamp_events", ["employee_id"], unique=False
    )
    op.create_index(op.f("ix_time_stamp_events_tenant_id"), "time_stamp_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_time_stamp_events_timestamp"), "time_stamp_events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_time_stamp_events_timestamp"), table_name="time_stamp_events")
    op.drop_index(op.f("ix_time_stamp_events_tenant_id"), table_name="time_stamp_events")
    op.drop_index(op.f("ix_time_stamp_events_employee_id"), table_name="time_stamp_events")
    op.drop_table("time_stamp_events")

    op.drop_index(op.f("ix_daily_time_accounts_date"), table_name="daily_time_accounts")
    op.drop_index(op.f("ix_daily_time_accounts_tenant_id"), table_name="daily_time_accounts")
    op.drop_index(op.f("ix_daily_time_accounts_employee_id"), table_name="daily_time_accounts")
    op.drop_table("daily_time_accounts")

    op.drop_index(op.f("ix_employees_tenant_id"), table_name="employees")
    op.drop_table("employees")

    op.drop_index(op.f("ix_working_time_models_tenant_id"), table_name="working_time_models")
    op.drop_table("working_time_models")

    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_table("tenants")

    bind = op.get_bind()
    sa.Enum(name="dailytimeaccountstatus").drop(bind, checkfirst=True)
    sa.Enum(name="timestampeventtype").drop(bind, checkfirst=True)
    sa.Enum(name="tenanttype").drop(bind, checkfirst=True)
    sa.Enum(name="userrole").drop(bind, checkfirst=True)
