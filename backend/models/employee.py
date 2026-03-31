from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    employee_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    employment_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=100, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    working_time_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("working_time_models.id"), nullable=True
    )
    workday_monday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_tuesday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_wednesday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_thursday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_friday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_saturday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    workday_sunday: Mapped[bool | None] = mapped_column(default=None, nullable=True)
    team: Mapped[str | None] = mapped_column(String(80), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="employees")
    user: Mapped["User"] = relationship(back_populates="employee")
    working_time_model: Mapped["WorkingTimeModel"] = relationship(back_populates="employees")
    time_stamp_events: Mapped[list["TimeStampEvent"]] = relationship(back_populates="employee")
    daily_time_accounts: Mapped[list["DailyTimeAccount"]] = relationship(back_populates="employee")
