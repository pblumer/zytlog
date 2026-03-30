from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    employees: Mapped[list["Employee"]] = relationship(back_populates="tenant")
    working_time_models: Mapped[list["WorkingTimeModel"]] = relationship(back_populates="tenant")
    time_stamp_events: Mapped[list["TimeStampEvent"]] = relationship(back_populates="tenant")
    daily_time_accounts: Mapped[list["DailyTimeAccount"]] = relationship(back_populates="tenant")
