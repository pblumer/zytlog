from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import TimeStampEventType


class TimeStampEvent(TimestampMixin, Base):
    __tablename__ = "time_stamp_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    type: Mapped[TimeStampEventType] = mapped_column(Enum(TimeStampEventType), nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="web", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="time_stamp_events")
    employee: Mapped["Employee"] = relationship(back_populates="time_stamp_events")
