import { useMemo, useState, type ReactElement } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import { ReportExportActions } from '../components/ReportExportActions';
import { TotalsBar } from '../components/TotalsBar';
import { useReportExport } from '../hooks/useReportExport';
import { useMonthReport } from '../hooks/useZytlogApi';
import type { DailyOverviewRow } from '../types/api';
import { formatMinutes } from '../utils/date';

const now = new Date();
const WEEKDAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const MONTH_LABELS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

type DayContextLabel = 'workday' | 'non_workday' | 'holiday';

function toIsoDate(year: number, month: number, day: number) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function getStatusLabel(status: DailyOverviewRow['status']) {
  switch (status) {
    case 'complete':
      return 'Complete';
    case 'incomplete':
      return 'Incomplete';
    case 'invalid':
      return 'Invalid';
    default:
      return 'No data';
  }
}

function getDayContext(day: DailyOverviewRow): DayContextLabel {
  if (day.is_holiday) return 'holiday';
  if (day.is_workday) return 'workday';
  return 'non_workday';
}

function monthShift(year: number, month: number, offset: number) {
  const shifted = new Date(Date.UTC(year, month - 1 + offset, 1));
  return { year: shifted.getUTCFullYear(), month: shifted.getUTCMonth() + 1 };
}

export function MonthPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialYear = Number(searchParams.get('year')) || now.getFullYear();
  const initialMonth = Number(searchParams.get('month')) || now.getMonth() + 1;
  const [year, setYear] = useState(initialYear);
  const [month, setMonth] = useState(initialMonth);
  const query = useMonthReport(year, month);
  const exporter = useReportExport();

  const monthTitle = `${MONTH_LABELS[month - 1]} ${year}`;
  const todayIso = now.toISOString().slice(0, 10);

  const syncParams = (nextYear: number, nextMonth: number) => {
    setYear(nextYear);
    setMonth(nextMonth);
    setSearchParams({ year: String(nextYear), month: String(nextMonth) });
  };

  const goPreviousMonth = () => {
    const next = monthShift(year, month, -1);
    syncParams(next.year, next.month);
  };

  const goNextMonth = () => {
    const next = monthShift(year, month, 1);
    syncParams(next.year, next.month);
  };

  const goToCurrentMonth = () => {
    syncParams(now.getFullYear(), now.getMonth() + 1);
  };

  const daysByDate = useMemo(() => {
    const mapping = new Map<string, DailyOverviewRow>();
    for (const day of query.data?.days ?? []) {
      mapping.set(day.date, day);
    }
    return mapping;
  }, [query.data?.days]);

  const contextCounters = useMemo(() => {
    const days = query.data?.days ?? [];
    return days.reduce(
      (acc, day) => {
        const context = getDayContext(day);
        acc[context] += 1;
        return acc;
      },
      { workday: 0, non_workday: 0, holiday: 0 },
    );
  }, [query.data?.days]);

  const calendarCells = useMemo(() => {
    const firstOfMonth = new Date(Date.UTC(year, month - 1, 1));
    const firstWeekday = (firstOfMonth.getUTCDay() + 6) % 7;
    const monthLength = new Date(Date.UTC(year, month, 0)).getUTCDate();
    const cells: ReactElement[] = [];

    for (let i = 0; i < firstWeekday; i += 1) {
      cells.push(<div key={`empty-${i}`} className="month-calendar-empty" aria-hidden="true" />);
    }

    for (let dayNumber = 1; dayNumber <= monthLength; dayNumber += 1) {
      const iso = toIsoDate(year, month, dayNumber);
      const day = daysByDate.get(iso);
      const status = day?.status ?? 'empty';
      const dayContext = day ? getDayContext(day) : 'non_workday';
      const holidayLabel = day?.is_holiday ? day.holiday_name : null;

      cells.push(
        <button
          key={iso}
          type="button"
          className={`month-day-tile month-day-tile-${status} ${iso === todayIso ? 'month-day-tile-today' : ''}`}
          onClick={() => navigate(`/day?date=${iso}`)}
          title={`${iso} · ${getStatusLabel(status)}${holidayLabel ? ` · ${holidayLabel}` : ''}`}
          aria-label={`${iso}. ${getStatusLabel(status)}. Actual ${day ? formatMinutes(day.actual_minutes) : '00:00'}.`}
          aria-current={iso === todayIso ? 'date' : undefined}
        >
          <div className="month-day-tile-head">
            <strong>{dayNumber}</strong>
            <span className={`month-day-status-dot month-day-status-dot-${status}`} aria-hidden="true" />
          </div>
          <div className="month-day-tile-main">{day ? formatMinutes(day.actual_minutes) : '—'}</div>
          <div className="month-day-tile-secondary">Target {day ? formatMinutes(day.target_minutes) : '—'}</div>
          <div className={`month-day-tile-balance ${day && day.balance_minutes > 0 ? 'balance-positive' : ''} ${day && day.balance_minutes < 0 ? 'balance-negative' : ''}`}>
            Balance {day ? formatMinutes(day.balance_minutes) : '—'}
          </div>
          <div className="month-day-context-row">
            <span className={`month-day-context month-day-context-${dayContext}`}>
              {dayContext === 'holiday' ? 'Holiday' : dayContext === 'workday' ? 'Workday' : 'Non-workday'}
            </span>
            {holidayLabel ? <span className="month-day-holiday-name">{holidayLabel}</span> : null}
          </div>
        </button>,
      );
    }

    return cells;
  }, [daysByDate, month, navigate, todayIso, year]);

  return (
    <>
      <PageHeader
        title="Month"
        subtitle="Monatskonsole mit Tageskontext und Zeiterfassungsstatus"
        actions={
          <>
            <button type="button" className="btn secondary" onClick={goPreviousMonth}>
              ← Previous
            </button>
            <button type="button" className="btn secondary" onClick={goToCurrentMonth}>
              Today
            </button>
            <button type="button" className="btn secondary" onClick={goNextMonth}>
              Next →
            </button>
            <ReportExportActions disabled={exporter.isExporting} onExport={(format) => void exporter.exportMonth(year, month, format)} />
          </>
        }
      />

      {exporter.error ? <ErrorState message={exporter.error} /> : null}
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load monthly report." /> : null}

      {query.data ? (
        <>
          <DataSection title={monthTitle}>
            <div className="grid">
              <SummaryCard title="Target" value={formatMinutes(query.data.totals.target_minutes)} />
              <SummaryCard title="Actual" value={formatMinutes(query.data.totals.actual_minutes)} />
              <SummaryCard title="Balance" value={formatMinutes(query.data.totals.balance_minutes)} />
              <SummaryCard title="Calendar Days" value={query.data.totals.days_total} />
            </div>

            <TotalsBar
              items={[
                { label: 'Complete', value: query.data.totals.days_complete },
                { label: 'Incomplete', value: query.data.totals.days_incomplete },
                { label: 'Invalid', value: query.data.totals.days_invalid },
                { label: 'No Data', value: query.data.totals.days_empty },
                { label: 'Holidays', value: contextCounters.holiday },
                { label: 'Workdays', value: contextCounters.workday },
              ]}
            />
          </DataSection>

          <DataSection title="Legend">
            <div className="month-legend-grid">
              <span><i className="month-day-status-dot month-day-status-dot-complete" />Complete</span>
              <span><i className="month-day-status-dot month-day-status-dot-incomplete" />Incomplete</span>
              <span><i className="month-day-status-dot month-day-status-dot-invalid" />Invalid</span>
              <span><i className="month-day-status-dot month-day-status-dot-empty" />No data</span>
              <span><i className="month-day-context month-day-context-holiday" />Holiday</span>
              <span><i className="month-day-context month-day-context-workday" />Workday</span>
              <span><i className="month-day-context month-day-context-non_workday" />Non-workday</span>
              <span><i className="month-day-context month-day-context-absence" />Reserved: future absences</span>
            </div>
          </DataSection>

          {query.data.days.length ? (
            <DataSection title="Calendar">
              <div className="month-calendar-grid">
                {WEEKDAY_LABELS.map((weekday) => (
                  <div key={weekday} className="month-calendar-weekday">
                    {weekday}
                  </div>
                ))}
                {calendarCells}
              </div>
            </DataSection>
          ) : (
            <EmptyState title="No rows for this month" description="No time data has been recorded for the selected month." />
          )}
        </>
      ) : null}
    </>
  );
}
