from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import EmploymentStatus


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    working_time_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("working_time_models.id"), nullable=True
    )
    employee_number: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[EmploymentStatus] = mapped_column(default=EmploymentStatus.ACTIVE, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="employees")
    user: Mapped["User"] = relationship(back_populates="employee")
    working_time_model: Mapped["WorkingTimeModel"] = relationship(back_populates="employees")
    time_stamp_events: Mapped[list["TimeStampEvent"]] = relationship(back_populates="employee")
    daily_time_accounts: Mapped[list["DailyTimeAccount"]] = relationship(back_populates="employee")
