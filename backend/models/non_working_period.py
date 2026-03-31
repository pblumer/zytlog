from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class NonWorkingPeriod(TimestampMixin, Base):
    __tablename__ = "non_working_periods"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "non_working_period_set_id",
            "name",
            "start_date",
            "end_date",
            name="uq_non_working_periods_set_named_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    non_working_period_set_id: Mapped[int] = mapped_column(ForeignKey("non_working_period_sets.id"), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="non_working_periods", foreign_keys=[tenant_id])
    period_set: Mapped["NonWorkingPeriodSet"] = relationship(back_populates="periods")
