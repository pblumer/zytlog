from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import WorkingTimeModelType


class WorkingTimeModel(TimestampMixin, Base):
    __tablename__ = "working_time_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[WorkingTimeModelType] = mapped_column(
        default=WorkingTimeModelType.FLEXIBLE,
        nullable=False,
    )
    expected_daily_hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    break_minutes_default: Mapped[int] = mapped_column(default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="working_time_models")
    employees: Mapped[list["Employee"]] = relationship(back_populates="working_time_model")
