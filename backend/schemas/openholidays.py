from datetime import date as DateType
from typing import Literal

from pydantic import Field, model_validator

from backend.schemas.common import BaseSchema

ImportMode = Literal["skip_existing", "replace_existing_in_range"]


class OpenHolidaysCountryRead(BaseSchema):
    iso_code: str
    name: str | None = None


class OpenHolidaysLanguageRead(BaseSchema):
    language_code: str
    name: str | None = None


class OpenHolidaysSubdivisionRead(BaseSchema):
    code: str
    name: str | None = None


class OpenHolidaysImportRequest(BaseSchema):
    country_iso_code: str = Field(min_length=2, max_length=2)
    subdivision_code: str | None = Field(default=None, max_length=20)
    language_code: str = Field(min_length=2, max_length=10)
    valid_from: DateType
    valid_to: DateType
    import_mode: ImportMode = "skip_existing"

    @model_validator(mode="after")
    def validate_date_range(self) -> "OpenHolidaysImportRequest":
        if self.valid_to < self.valid_from:
            raise ValueError("valid_to must be greater than or equal to valid_from")
        return self


class OpenHolidaysImportPreviewRow(BaseSchema):
    date: DateType
    name: str
    country_iso_code: str
    subdivision_code: str | None = None
    language_code: str
    source: str
    exists_in_holiday_set: bool
    existing_holiday_id: int | None = None
    action_hint: Literal["create", "skip", "replace"]


class OpenHolidaysImportPreviewResponse(BaseSchema):
    rows: list[OpenHolidaysImportPreviewRow]


class OpenHolidaysImportCommitResponse(BaseSchema):
    created: int
    skipped: int
    replaced: int
