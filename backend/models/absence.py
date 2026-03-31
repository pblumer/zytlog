from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.models.enums import AbsenceDurationType, AbsenceType


class Absence(TimestampMixin, Base):
    __tablename__ = "absences"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "employee_id",
            "start_date",
            "end_date",
            "absence_type",
            "duration_type",
            name="uq_absences_employee_exact",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    absence_type: Mapped[AbsenceType] = mapped_column(
        Enum(
            AbsenceType,
            name="absencetype",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_type: Mapped[AbsenceDurationType] = mapped_column(
        Enum(
            AbsenceDurationType,
            name="absencedurationtype",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="absences")
    employee: Mapped["Employee"] = relationship(back_populates="absences")
