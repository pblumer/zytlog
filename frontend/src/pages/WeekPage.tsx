import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import { ReportExportActions } from '../components/ReportExportActions';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { TotalsBar } from '../components/TotalsBar';
import { useReportExport } from '../hooks/useReportExport';
import { useWeekReport } from '../hooks/useZytlogApi';
import { formatMinutes, getIsoWeek } from '../utils/date';

const nowWeek = getIsoWeek(new Date());
const weekdayFormatter = new Intl.DateTimeFormat('de-DE', { weekday: 'short', timeZone: 'UTC' });
const dateFormatter = new Intl.DateTimeFormat('de-DE', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  timeZone: 'UTC',
});

function toLocalIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, '0');
  const day = `${value.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatWeekday(date: string): string {
  return weekdayFormatter.format(new Date(`${date}T00:00:00Z`)).replace('.', '');
}

function formatDateLabel(date: string): string {
  return dateFormatter.format(new Date(`${date}T00:00:00Z`));
}

function getBalanceClassName(balanceMinutes: number): string {
  if (balanceMinutes > 0) return 'balance-positive';
  if (balanceMinutes < 0) return 'balance-negative';
  return 'balance-neutral';
}

export function WeekPage() {
  const navigate = useNavigate();
  const [year, setYear] = useState(nowWeek.year);
  const [week, setWeek] = useState(nowWeek.week);
  const query = useWeekReport(year, week);
  const exporter = useReportExport();

  const currentDate = useMemo(() => toLocalIsoDate(new Date()), []);

  const weekLabel = query.data ? `KW ${query.data.iso_week} / ${query.data.iso_year}` : `KW ${week} / ${year}`;
  const completeCount = query.data?.totals.days_complete ?? 0;
  const incompleteCount = query.data?.totals.days_incomplete ?? 0;
  const invalidCount = query.data?.totals.days_invalid ?? 0;

  const openDay = (date: string) => {
    navigate(`/day?date=${date}`);
  };

  return (
    <>
      <PageHeader
        title="Woche"
        subtitle="Wöchentliche Übersicht"
        actions={
          <>
            <input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} min={1970} max={2100} aria-label="Jahr" />
            <input type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} min={1} max={53} aria-label="Kalenderwoche" />
            <ReportExportActions disabled={exporter.isExporting} onExport={(format) => void exporter.exportWeek(year, week, format)} />
          </>
        }
      />
      {exporter.error ? <ErrorState message={exporter.error} /> : null}
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Wochenreport konnte nicht geladen werden." /> : null}
      {query.data ? (
        <>
          <div className="grid">
            <SummaryCard title="Woche" value={weekLabel} hint={`${formatDateLabel(query.data.range_start)} – ${formatDateLabel(query.data.range_end)}`} />
            <SummaryCard title="Soll" value={formatMinutes(query.data.totals.target_minutes)} />
            <SummaryCard title="Ist" value={formatMinutes(query.data.totals.actual_minutes)} />
            <SummaryCard
              title="Saldo"
              value={<span className={getBalanceClassName(query.data.totals.balance_minutes)}>{formatMinutes(query.data.totals.balance_minutes)}</span>}
              hint="laufende Woche"
            />
          </div>

          <DataSection title="Wochenstatus">
            <TotalsBar
              items={[
                { label: 'Vollständig', value: completeCount },
                { label: 'Unvollständig', value: incompleteCount },
                { label: 'Ungültig', value: invalidCount },
                { label: 'Keine Daten', value: query.data.totals.days_empty },
              ]}
            />
            <div className="week-strip" role="list" aria-label="Woche als Schnellansicht">
              {query.data.days.map((day) => {
                const isToday = day.date === currentDate;
                return (
                  <button
                    key={day.date}
                    type="button"
                    className={`week-strip-cell week-strip-${day.status} ${isToday ? 'is-today' : ''}`.trim()}
                    onClick={() => openDay(day.date)}
                    title={`${formatWeekday(day.date)} ${formatDateLabel(day.date)} öffnen`}
                    aria-label={`${formatWeekday(day.date)} ${formatDateLabel(day.date)}. Status ${day.status}. Tag öffnen`}
                    aria-current={isToday ? 'date' : undefined}
                  >
                    <span>{formatWeekday(day.date)}</span>
                    <strong>{day.date.slice(8, 10)}</strong>
                  </button>
                );
              })}
            </div>
          </DataSection>

          <DataSection title="Tage dieser Woche">
            {query.data.days.length ? (
              <div className="table-wrap">
                <table className="table week-table">
                  <thead>
                    <tr>
                      <th>Tag</th>
                      <th>Datum</th>
                      <th>Status</th>
                      <th>Soll</th>
                      <th>Ist</th>
                      <th>Saldo</th>
                      <th>Ereignisse</th>
                      <th>Aktion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.days.map((day) => {
                      const isToday = day.date === currentDate;
                      const needsAttention = day.status === 'incomplete' || day.status === 'invalid';

                      return (
                        <tr key={day.date} className={`${isToday ? 'is-today' : ''} ${needsAttention ? 'needs-attention' : ''}`.trim()}>
                          <td data-label="Tag">{formatWeekday(day.date)}</td>
                          <td data-label="Datum">{formatDateLabel(day.date)}</td>
                          <td data-label="Status">
                            <TableStatusBadge status={day.status} />
                          </td>
                          <td className="time-value" data-label="Soll">{formatMinutes(day.target_minutes)}</td>
                          <td className="time-value" data-label="Ist">{formatMinutes(day.actual_minutes)}</td>
                          <td className={`time-value ${getBalanceClassName(day.balance_minutes)}`} data-label="Saldo">{formatMinutes(day.balance_minutes)}</td>
                          <td data-label="Ereignisse">{day.event_count}</td>
                          <td data-label="Aktion">
                            <button type="button" className="btn outline" onClick={() => openDay(day.date)} aria-label={`Tag ${formatDateLabel(day.date)} öffnen`}>
                              Tag öffnen
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="Keine Tage für diese Woche" description="Für die gewählte Woche wurden noch keine Zeiteinträge erfasst." />
            )}
          </DataSection>
        </>
      ) : null}
      {!query.data && !query.isLoading && !query.error ? (
        <EmptyState title="Keine Wochenübersicht verfügbar" description="Bitte wählen Sie eine gültige Kalenderwoche." />
      ) : null}
    </>
  );
}
