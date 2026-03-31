from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin
from backend.core.config import settings
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.schemas.openholidays import (
    OpenHolidaysCountryRead,
    OpenHolidaysImportCommitResponse,
    OpenHolidaysImportPreviewResponse,
    OpenHolidaysImportPreviewRow,
    OpenHolidaysImportRequest,
    OpenHolidaysLanguageRead,
    OpenHolidaysSubdivisionRead,
)
from backend.services.openholidays_import_service import OpenHolidaysImportService
from backend.services.openholidays_service import OpenHolidaysClient

router = APIRouter(prefix="/admin", tags=["admin-openholidays"])


def _client() -> OpenHolidaysClient:
    return OpenHolidaysClient(base_url=settings.openholidays_base_url)


@router.get("/openholidays/countries", response_model=list[OpenHolidaysCountryRead])
def list_openholidays_countries(
    _: AuthContext = Depends(require_admin),
) -> list[OpenHolidaysCountryRead]:
    return [OpenHolidaysCountryRead.model_validate(item) for item in _client().list_countries()]


@router.get("/openholidays/languages", response_model=list[OpenHolidaysLanguageRead])
def list_openholidays_languages(
    _: AuthContext = Depends(require_admin),
) -> list[OpenHolidaysLanguageRead]:
    return [OpenHolidaysLanguageRead.model_validate(item) for item in _client().list_languages()]


@router.get("/openholidays/subdivisions", response_model=list[OpenHolidaysSubdivisionRead])
def list_openholidays_subdivisions(
    country_iso_code: str = Query(alias="countryIsoCode", min_length=2, max_length=2),
    _: AuthContext = Depends(require_admin),
) -> list[OpenHolidaysSubdivisionRead]:
    return [
        OpenHolidaysSubdivisionRead.model_validate(item)
        for item in _client().list_subdivisions(country_iso_code)
    ]


@router.post(
    "/holiday-sets/{holiday_set_id}/import/openholidays/preview",
    response_model=OpenHolidaysImportPreviewResponse,
)
def preview_openholidays_import(
    holiday_set_id: int,
    payload: OpenHolidaysImportRequest,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> OpenHolidaysImportPreviewResponse:
    holidays = _client().fetch_public_holidays(
        country_code=payload.country_iso_code,
        subdivision_code=payload.subdivision_code,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        language_code=payload.language_code,
    )
    if not holidays:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keine Feiertage im gewählten Zeitraum gefunden")

    service = OpenHolidaysImportService(HolidayRepository(db), HolidaySetRepository(db))
    rows = service.preview_import(
        tenant_id=context.tenant_id,
        holiday_set_id=holiday_set_id,
        open_holidays=holidays,
        import_mode=payload.import_mode,
    )
    return OpenHolidaysImportPreviewResponse(
        rows=[OpenHolidaysImportPreviewRow.model_validate(row.__dict__) for row in rows]
    )


@router.post(
    "/holiday-sets/{holiday_set_id}/import/openholidays/commit",
    response_model=OpenHolidaysImportCommitResponse,
)
def commit_openholidays_import(
    holiday_set_id: int,
    payload: OpenHolidaysImportRequest,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> OpenHolidaysImportCommitResponse:
    holidays = _client().fetch_public_holidays(
        country_code=payload.country_iso_code,
        subdivision_code=payload.subdivision_code,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        language_code=payload.language_code,
    )
    service = OpenHolidaysImportService(HolidayRepository(db), HolidaySetRepository(db))
    result = service.commit_import(
        tenant_id=context.tenant_id,
        holiday_set_id=holiday_set_id,
        open_holidays=holidays,
        import_mode=payload.import_mode,
    )
    return OpenHolidaysImportCommitResponse.model_validate(result)
