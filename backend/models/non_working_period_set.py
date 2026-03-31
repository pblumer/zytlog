from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class NonWorkingPeriodSet(TimestampMixin, Base):
    __tablename__ = "non_working_period_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="non_working_period_sets", foreign_keys=[tenant_id])
    periods: Mapped[list["NonWorkingPeriod"]] = relationship(back_populates="period_set")
    employees: Mapped[list["Employee"]] = relationship(back_populates="non_working_period_set")
