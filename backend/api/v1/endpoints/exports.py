from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.models.employee import Employee
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.services.daily_account_service import DailyAccountService
from backend.services.export_service import ExportService
from backend.services.reporting_service import ReportingService

router = APIRouter(prefix="/exports", tags=["exports"])


def _resolve_employee(db: Session, context: AuthContext) -> Employee:
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return employee


def _reporting_service(db: Session) -> ReportingService:
    return ReportingService(DailyAccountService(TimeStampEventRepository(db)))


def _content_disposition(filename: str) -> str:
    return f'attachment; filename="{filename}"'


@router.get("/my/day")
def export_my_day_csv(
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    account = DailyAccountService(TimeStampEventRepository(db)).get_daily_account(
        tenant_id=context.tenant_id,
        employee=employee,
        target_date=date_value,
    )
    payload = ExportService().build_day_csv(account)
    filename = f"zytlog_day_{date_value.isoformat()}.csv"
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/week")
def export_my_week_csv(
    year: int = Query(ge=1970, le=2100),
    week: int = Query(ge=1, le=53),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_week_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        iso_year=year,
        iso_week=week,
    )
    payload = ExportService().build_period_csv(report.days, report.totals)
    filename = f"zytlog_week_{year}_w{week:02d}.csv"
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/month")
def export_my_month_csv(
    year: int = Query(ge=1970, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_month_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
        month=month,
    )
    payload = ExportService().build_period_csv(report.days, report.totals)
    filename = f"zytlog_month_{year}-{month:02d}.csv"
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/year")
def export_my_year_csv(
    year: int = Query(ge=1970, le=2100),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_year_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
    )
    payload = ExportService().build_year_csv(report)
    filename = f"zytlog_year_{year}.csv"
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/day/pdf")
def export_my_day_pdf(
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    account = DailyAccountService(TimeStampEventRepository(db)).get_daily_account(
        tenant_id=context.tenant_id,
        employee=employee,
        target_date=date_value,
    )
    payload = ExportService().build_day_pdf(
        title="Day Report",
        user_name=employee.user.full_name,
        tenant_name=employee.tenant.name,
        date_range_label=date_value.isoformat(),
        account=account,
    )
    filename = f"zytlog_day_{date_value.isoformat()}.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/week/pdf")
def export_my_week_pdf(
    year: int = Query(ge=1970, le=2100),
    week: int = Query(ge=1, le=53),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_week_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        iso_year=year,
        iso_week=week,
    )
    payload = ExportService().build_period_pdf(
        title="Week Report",
        user_name=employee.user.full_name,
        tenant_name=employee.tenant.name,
        date_range_label=f"{report.range_start.isoformat()} to {report.range_end.isoformat()}",
        days=report.days,
        totals=report.totals,
    )
    filename = f"zytlog_week_{year}_w{week:02d}.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/month/pdf")
def export_my_month_pdf(
    year: int = Query(ge=1970, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_month_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
        month=month,
    )
    payload = ExportService().build_period_pdf(
        title="Month Report",
        user_name=employee.user.full_name,
        tenant_name=employee.tenant.name,
        date_range_label=f"{report.range_start.isoformat()} to {report.range_end.isoformat()}",
        days=report.days,
        totals=report.totals,
    )
    filename = f"zytlog_month_{year}-{month:02d}.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )


@router.get("/my/year/pdf")
def export_my_year_pdf(
    year: int = Query(ge=1970, le=2100),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    report = _reporting_service(db).get_year_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
    )
    payload = ExportService().build_year_pdf(
        title="Year Report",
        user_name=employee.user.full_name,
        tenant_name=employee.tenant.name,
        date_range_label=f"{year}-01-01 to {year}-12-31",
        overview=report,
    )
    filename = f"zytlog_year_{year}.pdf"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(filename)},
    )
