import { useMemo, useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { getCalendarMonth } from '../api/endpoints';
import { useAuth } from '../auth/provider';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import { ReportExportActions } from '../components/ReportExportActions';
import { TotalsBar } from '../components/TotalsBar';
import { useReportExport } from '../hooks/useReportExport';
import { useYearReport } from '../hooks/useZytlogApi';
import type { CalendarMonthDay, MonthlySummaryRow } from '../types/api';
import { formatMinutes } from '../utils/date';
import { formatMinutesShort } from '../components/DashboardMonthCalendar';

const monthLabelFormatter = new Intl.DateTimeFormat('de-DE', { month: 'long', year: 'numeric' });

function getMonthOverallStatus(month: MonthlySummaryRow): 'valid' | 'incomplete' | 'invalid' {
  if (month.days_invalid > 0) return 'invalid';
  if (month.days_incomplete > 0 || month.days_empty > 0) return 'incomplete';
  return 'valid';
}

function getDayDotStatus(day: CalendarMonthDay): 'valid' | 'incomplete' | 'invalid' | 'empty' {
  if (day.status === 'invalid') return 'invalid';
  if (day.status === 'incomplete') return 'incomplete';
  if (day.status === 'complete') return 'valid';
  return 'empty';
}

function formatAbsenceLabel(day: CalendarMonthDay): string | null {
  if (!day.absence) return null;
  const durationHint = day.absence.duration_type === 'half_day_am' ? ' (AM)' : day.absence.duration_type === 'half_day_pm' ? ' (PM)' : '';
  return `${day.absence.label}${durationHint}`;
}

function getAbsenceLayers(day: CalendarMonthDay): Array<'left' | 'right'> {
  if (!day.absence) return [];
  if (day.absence.duration_type === 'half_day_am') return ['left'];
  if (day.absence.duration_type === 'half_day_pm') return ['right'];
  return ['left', 'right'];
}

function formatNonWorkingPeriodLabel(day: CalendarMonthDay): string | null {
  if (!day.is_in_non_working_period) return null;
  return day.non_working_period_label
    ? `Arbeitsfreier Zeitraum: ${day.non_working_period_label}`
    : 'Arbeitsfreier Zeitraum';
}

export function YearPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [year, setYear] = useState(new Date().getFullYear());
  const query = useYearReport(year);
  const exporter = useReportExport();

  const monthNumbers = useMemo(() => Array.from({ length: 12 }, (_, index) => index + 1), []);
  const calendarQueries = useQueries({
    queries: monthNumbers.map((month) => ({
      queryKey: ['calendar-month', year, month],
      queryFn: () => getCalendarMonth(year, month, token),
      staleTime: 60_000,
    })),
  });

  const monthCalendars = useMemo(() => {
    const byMonth = new Map<number, CalendarMonthDay[]>();
    calendarQueries.forEach((calendarQuery, index) => {
      if (calendarQuery.data) {
        byMonth.set(monthNumbers[index], calendarQuery.data.days);
      }
    });
    return byMonth;
  }, [calendarQueries, monthNumbers]);

  const isCalendarLoading = calendarQueries.some((calendarQuery) => calendarQuery.isLoading);
  const hasCalendarError = calendarQueries.some((calendarQuery) => calendarQuery.isError);

  // Compute YTD: sum months up to and including the current month (if viewing current year)
  const ytd = useMemo(() => {
    if (!query.data) return null;
    const now = new Date();
    const isCurrentYear = year === now.getFullYear();
    const cutoffMonth = isCurrentYear ? now.getMonth() + 1 : year < now.getFullYear() ? 12 : 0;
    let target = 0;
    let actual = 0;
    let balance = 0;
    let daysTotal = 0;
    let daysComplete = 0;
    let daysIncomplete = 0;
    let daysInvalid = 0;
    let daysEmpty = 0;
    for (const m of query.data.months) {
      if (m.month <= cutoffMonth) {
        target += m.target_minutes;
        actual += m.actual_minutes;
        balance += m.balance_minutes;
        daysTotal += m.days_total;
        daysComplete += m.days_complete;
        daysIncomplete += m.days_incomplete;
        daysInvalid += m.days_invalid;
        daysEmpty += m.days_empty;
      }
    }
    return { target_minutes: target, actual_minutes: actual, balance_minutes: balance, days_total: daysTotal, days_complete: daysComplete, days_incomplete: daysIncomplete, days_invalid: daysInvalid, days_empty: daysEmpty };
  }, [query.data, year]);

  return (
    <>
      <PageHeader
        title="Year"
        subtitle="Yearly totals"
        actions={
          <>
            <input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} min={1970} max={2100} />
            <ReportExportActions disabled={exporter.isExporting} onExport={(format) => void exporter.exportYear(year, format)} />
          </>
        }
      />
      {exporter.error ? <ErrorState message={exporter.error} /> : null}
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load yearly report." /> : null}
      {!query.isLoading && !query.error && isCalendarLoading ? <LoadingBlock /> : null}
      {hasCalendarError ? <ErrorState message="Could not load yearly day statuses." /> : null}
      {query.data ? (
        <>
          <div className="grid">
            <SummaryCard title="Jahresziel Soll" value={formatMinutes(query.data.totals.target_minutes)} />
            <SummaryCard title="YTD Soll" value={ytd ? formatMinutes(ytd.target_minutes) : '–'} />
            <SummaryCard title="YTD Ist" value={ytd ? formatMinutes(ytd.actual_minutes) : '–'} />
            <SummaryCard
              title="YTD Saldo"
              value={ytd ? `${ytd.balance_minutes > 0 ? '+' : ''}${formatMinutes(ytd.balance_minutes)}` : '–'}
              className={ytd ? (ytd.balance_minutes > 0 ? 'summary-balance-positive' : ytd.balance_minutes < 0 ? 'summary-balance-negative' : '') : ''}
              hint={ytd ? (ytd.balance_minutes > 0 ? 'Ueberzeit' : ytd.balance_minutes < 0 ? 'Minuszeit' : 'Ausgeglichen') : undefined}
            />
          </div>
          <DataSection title="Monthly Summary">
            <TotalsBar
              items={[
                { label: 'Complete', value: query.data.totals.days_complete },
                { label: 'Incomplete', value: query.data.totals.days_incomplete },
                { label: 'Invalid', value: query.data.totals.days_invalid },
                { label: 'Empty', value: query.data.totals.days_empty },
              ]}
            />
            {query.data.months.length ? (
              <div className="year-month-grid" role="list" aria-label={`Monthly overview for ${year}`}>
                {query.data.months.map((month) => {
                  const monthDate = new Date(year, month.month - 1, 1);
                  const monthTitle = monthLabelFormatter.format(monthDate);
                  const overallStatus = getMonthOverallStatus(month);
                  const balanceClass = month.balance_minutes > 0 ? 'balance-positive' : month.balance_minutes < 0 ? 'balance-negative' : 'balance-neutral';
                  const monthDays = monthCalendars.get(month.month) ?? [];
                  const firstOfMonth = new Date(Date.UTC(year, month.month - 1, 1));
                  const firstWeekday = (firstOfMonth.getUTCDay() + 6) % 7;

                  return (
                    <button
                      key={month.month}
                      className="year-month-card"
                      type="button"
                      role="listitem"
                      onClick={() => navigate(`/month?year=${year}&month=${month.month}`)}
                      aria-label={`${monthTitle}. Status: ${overallStatus}. Soll ${formatMinutes(month.target_minutes)}, Ist ${formatMinutes(month.actual_minutes)}, Saldo ${formatMinutes(month.balance_minutes)}.`}
                      title="Open month details"
                    >
                      <div className="year-month-card-header">
                        <h3>{monthTitle}</h3>
                        <span className={`year-status-pill year-status-${overallStatus}`}>
                          <span aria-hidden="true" className="year-status-dot" />
                          <span>{overallStatus === 'valid' ? 'OK' : overallStatus === 'incomplete' ? 'Unvollständig' : 'Fehlerhaft'}</span>
                        </span>
                      </div>

                      <dl className="year-month-summary">
                        <div>
                          <dt>Soll</dt>
                          <dd>{formatMinutes(month.target_minutes)}</dd>
                        </div>
                        <div>
                          <dt>Ist</dt>
                          <dd>{formatMinutes(month.actual_minutes)}</dd>
                        </div>
                        <div>
                          <dt>Saldo</dt>
                          <dd className={balanceClass}>
                            {month.balance_minutes > 0 ? '+' : ''}{formatMinutes(month.balance_minutes)}
                          </dd>
                        </div>
                      </dl>

                      <div className="year-mini-grid-wrap">
                        <div className="year-mini-grid">
                          {(() => {
                            const elements: React.ReactNode[] = [];
                            let weekBalance = 0;
                            let weekRow = 2; // row 1 = weekday headers
                            let colIdx = 0; // 0=Mon .. 6=Sun

                            // Weekday header row
                            const dayLabels = ['M', 'D', 'M', 'D', 'F', 'S', 'S'];
                            dayLabels.forEach((label, i) => {
                              elements.push(
                                <span key={`wh-${i}`} className="year-mini-weekday" aria-hidden="true" style={{ gridColumn: i + 1, gridRow: 1 }}>{label}</span>
                              );
                            });

                            // Placeholders for days before the 1st
                            for (let i = 0; i < firstWeekday; i++) {
                              elements.push(
                                <span key={`ph-${i}`} className="year-mini-dot year-mini-dot-placeholder" aria-hidden="true" style={{ gridColumn: i + 1, gridRow: weekRow }} />
                              );
                              colIdx = i + 1;
                            }

                            monthDays.forEach((day, dayIdx) => {
                              const dotStatus = getDayDotStatus(day);
                              const absenceLabel = formatAbsenceLabel(day);
                              const absenceLayers = getAbsenceLayers(day);
                              const nonWorkingPeriodLabel = formatNonWorkingPeriodLabel(day);
                              const hasAbsence = absenceLayers.length > 0;
                              const showNonWorkingPeriodStyle = !hasAbsence && day.is_in_non_working_period;
                              const visualStatusClass = showNonWorkingPeriodStyle ? 'year-mini-dot-non-working-period' : `year-mini-dot-${dotStatus}`;
                              const contextParts = [dotStatus, absenceLabel, nonWorkingPeriodLabel].filter(Boolean);
                              const contextLabel = contextParts.join(' · ');
                              const actualLabel = formatMinutesShort(day.actual_minutes);
                              const balanceLabel = day.balance_minutes !== 0 ? `${day.balance_minutes > 0 ? '+' : ''}${formatMinutesShort(day.balance_minutes)}` : '';
                              const balanceBarClass = day.balance_minutes > 0 ? 'year-mini-bar-pos' : day.balance_minutes < 0 ? 'year-mini-bar-neg' : '';
                              const balanceTextClass = day.balance_minutes > 0 ? 'year-mini-saldo-pos' : day.balance_minutes < 0 ? 'year-mini-saldo-neg' : '';
                              const isAbsence = hasAbsence || showNonWorkingPeriodStyle;

                              weekBalance += day.balance_minutes;
                              colIdx += 1;

                              const hasActualHours = day.actual_minutes > 0;

                              elements.push(
                                <span
                                  key={day.date}
                                  role="img"
                                  aria-label={`${day.date}: ${contextLabel}, Ist ${actualLabel || '0:00'}, Saldo ${balanceLabel || '0:00'}`}
                                  className={`year-mini-dot ${visualStatusClass}${isAbsence ? ' year-mini-dot-light' : ''}`}
                                  title={`${day.date}: Ist ${actualLabel || '0:00'}, Saldo ${balanceLabel || '0:00'}`}
                                  style={{ gridColumn: colIdx, gridRow: weekRow }}
                                >
                                  {absenceLayers.map((side) => (
                                    <span
                                      key={side}
                                      className={`year-mini-dot-absence-layer year-mini-dot-absence-${side} year-mini-dot-absence-${day.absence?.type}`}
                                    />
                                  ))}
                                  <span className="year-mini-dot-actual">{actualLabel || ''}</span>
                                  {hasActualHours && day.balance_minutes !== 0 && <span className={`year-mini-dot-balance ${balanceBarClass}`} />}
                                  {hasActualHours && balanceLabel && <span className={`year-mini-dot-saldo ${balanceTextClass}`}>{balanceLabel}</span>}
                                </span>
                              );

                              // End of week (Sunday) or last day of month
                              const isEndOfWeek = colIdx === 7;
                              const isLastDay = dayIdx === monthDays.length - 1;

                              if (isEndOfWeek || isLastDay) {
                                // Weekly balance row
                                const weekBalLabel = formatMinutesShort(Math.abs(weekBalance));
                                const prefix = weekBalance > 0 ? '+' : weekBalance < 0 ? '-' : '';
                                const weekClass = weekBalance > 0 ? 'year-week-balance-pos' : weekBalance < 0 ? 'year-week-balance-neg' : 'year-week-balance-zero';
                                weekRow += 1;
                                elements.push(
                                  <span key={`wb-${month.month}-${dayIdx}`} className="year-week-balance-row" style={{ gridRow: weekRow }} aria-label={`Wochensaldo: ${prefix}${weekBalLabel}`}>
                                    <span className={`year-week-balance ${weekClass}`}>
                                      {prefix}{weekBalLabel}
                                    </span>
                                  </span>
                                );
                                weekBalance = 0;
                                weekRow += 1;
                                colIdx = 0;
                              }
                            });
                            return elements;
                          })()}
                        </div>
                      </div>

                      <p className="year-month-meta">{month.days_total} Tage</p>
                    </button>
                  );
                })}
              </div>
            ) : (
              <EmptyState title="No rows for this year" description="No time data has been recorded for the selected year." />
            )}
          </DataSection>
        </>
      ) : null}
    </>
  );
}
