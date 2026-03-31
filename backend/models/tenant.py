from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import TenantType


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    type: Mapped[TenantType] = mapped_column(Enum(TenantType), default=TenantType.COMPANY, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    default_holiday_set_id: Mapped[int | None] = mapped_column(ForeignKey("holiday_sets.id"), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    employees: Mapped[list["Employee"]] = relationship(back_populates="tenant")
    working_time_models: Mapped[list["WorkingTimeModel"]] = relationship(back_populates="tenant")
    time_stamp_events: Mapped[list["TimeStampEvent"]] = relationship(back_populates="tenant")
    daily_time_accounts: Mapped[list["DailyTimeAccount"]] = relationship(back_populates="tenant")
    holidays: Mapped[list["Holiday"]] = relationship(back_populates="tenant")
    holiday_sets: Mapped[list["HolidaySet"]] = relationship(
        back_populates="tenant",
        foreign_keys="HolidaySet.tenant_id",
    )
    default_holiday_set: Mapped["HolidaySet | None"] = relationship(
        foreign_keys=[default_holiday_set_id],
        post_update=True,
    )
