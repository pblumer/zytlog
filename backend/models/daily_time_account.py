from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class DailyTimeAccount(TimestampMixin, Base):
    __tablename__ = "daily_time_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    account_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    planned_minutes: Mapped[int] = mapped_column(nullable=False)
    worked_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    break_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    delta_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    balance_minutes: Mapped[int] = mapped_column(default=0, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="daily_time_accounts")
    employee: Mapped["Employee"] = relationship(back_populates="daily_time_accounts")
