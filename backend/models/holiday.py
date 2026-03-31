from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Holiday(TimestampMixin, Base):
    __tablename__ = "holidays"
    __table_args__ = (UniqueConstraint("tenant_id", "date", name="uq_holidays_tenant_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="holidays")
