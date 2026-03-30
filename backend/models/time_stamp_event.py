from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import TimeStampEventType


class TimeStampEvent(TimestampMixin, Base):
    __tablename__ = "time_stamp_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    event_type: Mapped[TimeStampEventType] = mapped_column(nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), default="web", nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="time_stamp_events")
    employee: Mapped["Employee"] = relationship(back_populates="time_stamp_events")
