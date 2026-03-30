from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class WorkingTimeModel(TimestampMixin, Base):
    __tablename__ = "working_time_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weekly_target_hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    workdays_per_week: Mapped[int] = mapped_column(default=5, nullable=False)
    annual_target_hours: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="working_time_models")
    employees: Mapped[list["Employee"]] = relationship(back_populates="working_time_model")
