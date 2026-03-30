from __future__ import annotations

import csv
from datetime import date, datetime
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.schemas.time_tracking import (
    DailyOverviewRow,
    DailyTimeAccountRead,
    MonthlyOverviewRead,
    MonthlySummaryRow,
    OverviewTotals,
    WeeklyOverviewRead,
    YearlyOverviewRead,
)


class ExportService:
    def format_minutes_hhmm(self, minutes: int) -> str:
        sign = "-" if minutes < 0 else ""
        absolute = abs(minutes)
        return f"{sign}{absolute // 60:02d}:{absolute % 60:02d}"

    def build_day_csv(self, account: DailyTimeAccountRead) -> bytes:
        headers = [
            "Date",
            "Status",
            "Target Minutes",
            "Target HH:MM",
            "Actual Minutes",
            "Actual HH:MM",
            "Break Minutes",
            "Break HH:MM",
            "Balance Minutes",
            "Balance HH:MM",
            "Event Count",
        ]
        rows = [
            [
                account.date.isoformat(),
                account.status.value,
                account.target_minutes,
                self.format_minutes_hhmm(account.target_minutes),
                account.actual_minutes,
                self.format_minutes_hhmm(account.actual_minutes),
                account.break_minutes,
                self.format_minutes_hhmm(account.break_minutes),
                account.balance_minutes,
                self.format_minutes_hhmm(account.balance_minutes),
                account.event_count,
            ],
            [
                "TOTAL",
                "",
                account.target_minutes,
                self.format_minutes_hhmm(account.target_minutes),
                account.actual_minutes,
                self.format_minutes_hhmm(account.actual_minutes),
                account.break_minutes,
                self.format_minutes_hhmm(account.break_minutes),
                account.balance_minutes,
                self.format_minutes_hhmm(account.balance_minutes),
                account.event_count,
            ],
        ]
        return self._to_csv_bytes(headers, rows)

    def build_period_csv(self, days: list[DailyOverviewRow], totals: OverviewTotals) -> bytes:
        headers = [
            "Date",
            "Status",
            "Target Minutes",
            "Target HH:MM",
            "Actual Minutes",
            "Actual HH:MM",
            "Break Minutes",
            "Break HH:MM",
            "Balance Minutes",
            "Balance HH:MM",
            "Event Count",
        ]
        rows = [
            [
                row.date.isoformat(),
                row.status.value,
                row.target_minutes,
                self.format_minutes_hhmm(row.target_minutes),
                row.actual_minutes,
                self.format_minutes_hhmm(row.actual_minutes),
                row.break_minutes,
                self.format_minutes_hhmm(row.break_minutes),
                row.balance_minutes,
                self.format_minutes_hhmm(row.balance_minutes),
                row.event_count,
            ]
            for row in days
        ]
        rows.append(
            [
                "TOTAL",
                "",
                totals.target_minutes,
                self.format_minutes_hhmm(totals.target_minutes),
                totals.actual_minutes,
                self.format_minutes_hhmm(totals.actual_minutes),
                totals.break_minutes,
                self.format_minutes_hhmm(totals.break_minutes),
                totals.balance_minutes,
                self.format_minutes_hhmm(totals.balance_minutes),
                totals.days_total,
            ]
        )
        return self._to_csv_bytes(headers, rows)

    def build_year_csv(self, year_overview: YearlyOverviewRead) -> bytes:
        headers = [
            "Month",
            "Target Minutes",
            "Target HH:MM",
            "Actual Minutes",
            "Actual HH:MM",
            "Break Minutes",
            "Break HH:MM",
            "Balance Minutes",
            "Balance HH:MM",
            "Days Total",
            "Days Complete",
            "Days Incomplete",
            "Days Invalid",
            "Days Empty",
        ]
        rows = [
            self._year_row(year_overview.year, month)
            for month in year_overview.months
        ]
        totals = year_overview.totals
        rows.append(
            [
                "TOTAL",
                totals.target_minutes,
                self.format_minutes_hhmm(totals.target_minutes),
                totals.actual_minutes,
                self.format_minutes_hhmm(totals.actual_minutes),
                totals.break_minutes,
                self.format_minutes_hhmm(totals.break_minutes),
                totals.balance_minutes,
                self.format_minutes_hhmm(totals.balance_minutes),
                totals.days_total,
                totals.days_complete,
                totals.days_incomplete,
                totals.days_invalid,
                totals.days_empty,
            ]
        )
        return self._to_csv_bytes(headers, rows)

    def build_day_pdf(
        self,
        *,
        title: str,
        user_name: str,
        tenant_name: str,
        date_range_label: str,
        account: DailyTimeAccountRead,
    ) -> bytes:
        headers = ["Date", "Status", "Target", "Actual", "Break", "Balance", "Events"]
        rows = [
            [
                account.date.isoformat(),
                account.status.value,
                self._minutes_display(account.target_minutes),
                self._minutes_display(account.actual_minutes),
                self._minutes_display(account.break_minutes),
                self._minutes_display(account.balance_minutes),
                str(account.event_count),
            ]
        ]
        return self._build_pdf(
            title=title,
            user_name=user_name,
            tenant_name=tenant_name,
            date_range_label=date_range_label,
            headers=headers,
            rows=rows,
            totals=account,
        )

    def build_period_pdf(
        self,
        *,
        title: str,
        user_name: str,
        tenant_name: str,
        date_range_label: str,
        days: list[DailyOverviewRow],
        totals: OverviewTotals,
    ) -> bytes:
        headers = ["Date", "Status", "Target", "Actual", "Break", "Balance", "Events"]
        rows = [
            [
                row.date.isoformat(),
                row.status.value,
                self._minutes_display(row.target_minutes),
                self._minutes_display(row.actual_minutes),
                self._minutes_display(row.break_minutes),
                self._minutes_display(row.balance_minutes),
                str(row.event_count),
            ]
            for row in days
        ]
        return self._build_pdf(
            title=title,
            user_name=user_name,
            tenant_name=tenant_name,
            date_range_label=date_range_label,
            headers=headers,
            rows=rows,
            totals=totals,
        )

    def build_year_pdf(
        self,
        *,
        title: str,
        user_name: str,
        tenant_name: str,
        date_range_label: str,
        overview: YearlyOverviewRead,
    ) -> bytes:
        headers = ["Month", "Target", "Actual", "Break", "Balance", "Days"]
        rows = [
            [
                f"{overview.year}-{month.month:02d}",
                self._minutes_display(month.target_minutes),
                self._minutes_display(month.actual_minutes),
                self._minutes_display(month.break_minutes),
                self._minutes_display(month.balance_minutes),
                str(month.days_total),
            ]
            for month in overview.months
        ]
        return self._build_pdf(
            title=title,
            user_name=user_name,
            tenant_name=tenant_name,
            date_range_label=date_range_label,
            headers=headers,
            rows=rows,
            totals=overview.totals,
        )

    def _build_pdf(
        self,
        *,
        title: str,
        user_name: str,
        tenant_name: str,
        date_range_label: str,
        headers: list[str],
        rows: list[list[str]],
        totals: OverviewTotals | DailyTimeAccountRead,
    ) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        elements = [
            Paragraph(title, styles["Title"]),
            Paragraph(f"User: {user_name}", styles["Normal"]),
            Paragraph(f"Tenant: {tenant_name}", styles["Normal"]),
            Paragraph(f"Date range: {date_range_label}", styles["Normal"]),
            Spacer(1, 12),
        ]

        table = Table([headers, *rows], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e9f0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

        elements.extend(self._build_totals_paragraphs(styles, totals))
        elements.append(Spacer(1, 8))
        elements.append(
            Paragraph(f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Italic"])
        )

        document.build(elements)
        return buffer.getvalue()

    def _build_totals_paragraphs(self, styles, totals: OverviewTotals | DailyTimeAccountRead) -> list[Paragraph]:
        if isinstance(totals, DailyTimeAccountRead):
            return [
                Paragraph("Totals", styles["Heading3"]),
                Paragraph(
                    f"Target: {self._minutes_display(totals.target_minutes)} | "
                    f"Actual: {self._minutes_display(totals.actual_minutes)} | "
                    f"Break: {self._minutes_display(totals.break_minutes)} | "
                    f"Balance: {self._minutes_display(totals.balance_minutes)} | "
                    f"Events: {totals.event_count}",
                    styles["Normal"],
                ),
            ]
        return [
            Paragraph("Totals", styles["Heading3"]),
            Paragraph(
                f"Target: {self._minutes_display(totals.target_minutes)} | "
                f"Actual: {self._minutes_display(totals.actual_minutes)} | "
                f"Break: {self._minutes_display(totals.break_minutes)} | "
                f"Balance: {self._minutes_display(totals.balance_minutes)}",
                styles["Normal"],
            ),
            Paragraph(
                f"Days total: {totals.days_total} | Complete: {totals.days_complete} | "
                f"Incomplete: {totals.days_incomplete} | Invalid: {totals.days_invalid} | Empty: {totals.days_empty}",
                styles["Normal"],
            ),
        ]

    def _year_row(self, year: int, month: MonthlySummaryRow) -> list[str | int]:
        return [
            f"{year}-{month.month:02d}",
            month.target_minutes,
            self.format_minutes_hhmm(month.target_minutes),
            month.actual_minutes,
            self.format_minutes_hhmm(month.actual_minutes),
            month.break_minutes,
            self.format_minutes_hhmm(month.break_minutes),
            month.balance_minutes,
            self.format_minutes_hhmm(month.balance_minutes),
            month.days_total,
            month.days_complete,
            month.days_incomplete,
            month.days_invalid,
            month.days_empty,
        ]

    def _minutes_display(self, minutes: int) -> str:
        return f"{minutes} min ({self.format_minutes_hhmm(minutes)})"

    def _to_csv_bytes(self, headers: list[str], rows: list[list[str | int]]) -> bytes:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return output.getvalue().encode("utf-8-sig")
