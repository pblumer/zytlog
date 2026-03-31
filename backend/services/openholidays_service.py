from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpenHolidayItem:
    date: date
    name: str
    country_iso_code: str
    subdivision_code: str | None
    language_code: str
    source_reference: str


class OpenHolidaysClient:
    def __init__(self, *, base_url: str, timeout_seconds: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def list_countries(self) -> list[dict[str, str | None]]:
        payload = self._fetch_json("/Countries")
        rows: list[dict[str, str | None]] = []
        for item in payload:
            iso_code = item.get("isoCode")
            name = self._get_localized_name(item.get("name") or [])
            if isinstance(iso_code, str):
                rows.append({"iso_code": iso_code, "name": name})
        rows.sort(key=lambda entry: (entry["name"] or entry["iso_code"] or ""))
        return rows

    def list_languages(self) -> list[dict[str, str | None]]:
        payload = self._fetch_json("/Languages")
        rows: list[dict[str, str | None]] = []
        for item in payload:
            iso_code = item.get("isoCode")
            name = self._get_localized_name(item.get("name") or [])
            if isinstance(iso_code, str):
                rows.append({"language_code": iso_code, "name": name})
        rows.sort(key=lambda entry: (entry["name"] or entry["language_code"] or ""))
        return rows

    def list_subdivisions(self, country_code: str) -> list[dict[str, str | None]]:
        payload = self._fetch_json(
            f"/Subdivisions/{country_code.upper()}",
            error_detail="Regionen/Subdivisions konnten nicht geladen werden.",
        )
        rows: list[dict[str, str | None]] = []
        for item in payload:
            code = item.get("code")
            name = self._get_localized_name(item.get("name") or [])
            if isinstance(code, str):
                rows.append({"code": code, "name": name})
        rows.sort(key=lambda entry: (entry["name"] or entry["code"] or ""))
        return rows

    def fetch_public_holidays(
        self,
        *,
        country_code: str,
        subdivision_code: str | None,
        valid_from: date,
        valid_to: date,
        language_code: str,
    ) -> list[OpenHolidayItem]:
        query = {
            "countryIsoCode": country_code.upper(),
            "validFrom": valid_from.isoformat(),
            "validTo": valid_to.isoformat(),
            "languageIsoCode": language_code,
        }
        if subdivision_code:
            query["subdivisionCode"] = subdivision_code
        payload = self._fetch_json(f"/PublicHolidays?{urlencode(query)}")

        holidays: list[OpenHolidayItem] = []
        for row in payload:
            start_date = row.get("startDate")
            if not isinstance(start_date, str):
                continue
            try:
                holiday_date = date.fromisoformat(start_date)
            except ValueError:
                continue
            name = self._pick_name_by_language(row.get("name") or [], language_code)
            if not name:
                continue
            holidays.append(
                OpenHolidayItem(
                    date=holiday_date,
                    name=name,
                    country_iso_code=country_code.upper(),
                    subdivision_code=subdivision_code,
                    language_code=language_code,
                    source_reference=str(row.get("id") or f"{country_code.upper()}-{start_date}-{name}"),
                )
            )
        holidays.sort(key=lambda holiday: holiday.date)
        return holidays

    def _fetch_json(self, path: str, *, error_detail: str | None = None) -> Any:
        target_url = f"{self.base_url}{path}"
        try:
            with urlopen(target_url, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            logger.warning(
                "OpenHolidays request failed with HTTP status.",
                extra={
                    "target_url": target_url,
                    "status_code": exc.code,
                    "response_body": response_body[:500],
                },
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail or "OpenHolidays konnte nicht erreicht werden. Bitte später erneut versuchen.",
            ) from exc
        except URLError as exc:
            logger.warning(
                "OpenHolidays request failed with network error.",
                extra={"target_url": target_url, "reason": str(exc.reason)},
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail or "OpenHolidays konnte nicht erreicht werden. Bitte später erneut versuchen.",
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("OpenHolidays request failed unexpectedly.", extra={"target_url": target_url})
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_detail or "OpenHolidays konnte nicht erreicht werden. Bitte später erneut versuchen.",
            ) from exc

    @staticmethod
    def _get_localized_name(values: list[dict[str, Any]]) -> str | None:
        if not values:
            return None
        first = values[0]
        text = first.get("text")
        return text if isinstance(text, str) else None

    @staticmethod
    def _pick_name_by_language(values: list[dict[str, Any]], language_code: str) -> str | None:
        normalized = language_code.lower()
        for entry in values:
            if str(entry.get("language")) == normalized:
                text = entry.get("text")
                if isinstance(text, str) and text:
                    return text
        for entry in values:
            text = entry.get("text")
            if isinstance(text, str) and text:
                return text
        return None
