import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { DashboardMonthCalendar } from '../components/DashboardMonthCalendar';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { QuickStampCard } from '../components/QuickStampCard';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useCurrentStatus, useDailyAccount, useDashboardCalendarMonth, useTimeStamps } from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

export function MyTimePage() {
  const now = new Date();
  const [monthCursor, setMonthCursor] = useState({ year: now.getFullYear(), month: now.getMonth() + 1 });
  const [selectedDate, setSelectedDate] = useState(isoDate(now));

  const currentStatus = useCurrentStatus();
  const selectedDayAccount = useDailyAccount(selectedDate);
  const selectedDayEvents = useTimeStamps(selectedDate, selectedDate);
  const calendar = useDashboardCalendarMonth(monthCursor.year, monthCursor.month);

  const columns = useMemo<DataGridColumn<TimeStampEvent>[]>(
    () => [
      { id: 'type', header: 'Typ', cell: (row) => <TableStatusBadge status={row.type} />, sortValue: (row) => row.type, searchableText: (row) => row.type, sortable: true },
      { id: 'timestamp', header: 'Zeitpunkt', cell: (row) => formatDateTime(row.timestamp), sortValue: (row) => row.timestamp, searchableText: (row) => row.timestamp, sortable: true },
      { id: 'source', header: 'Quelle', cell: (row) => row.source, sortValue: (row) => row.source, searchableText: (row) => row.source, sortable: true },
      { id: 'comment', header: 'Kommentar', cell: (row) => row.comment ?? '—', searchableText: (row) => row.comment ?? '' },
    ],
    [],
  );

  if (currentStatus.isLoading || selectedDayAccount.isLoading || selectedDayEvents.isLoading || calendar.isLoading) return <LoadingBlock />;
  if (currentStatus.error || selectedDayAccount.error || selectedDayEvents.error || calendar.error) return <ErrorState message="Zeitdaten konnten nicht geladen werden." />;

  const activeStatus = currentStatus.data?.status ?? 'clocked_out';
  const selectedAbsence = selectedDayAccount.data?.absence;
  const selectedAbsenceLabel = selectedAbsence
    ? `${selectedAbsence.label}${selectedAbsence.duration_type === 'half_day_am' ? ' (AM)' : selectedAbsence.duration_type === 'half_day_pm' ? ' (PM)' : ''}`
    : '—';

  return (
    <>
      <PageHeader title="Meine Zeit" subtitle="Schneller Tageszugriff und Monatsinspektion" />

      <QuickStampCard status={activeStatus} lastEventTimestamp={currentStatus.data?.last_event_timestamp} />

      <section className="grid" style={{ marginTop: '1rem' }} aria-label="Zusammenfassung ausgewählter Tag">
        <SummaryCard title="Ausgewählter Tag" value={selectedDate} hint={<TableStatusBadge status={selectedDayAccount.data?.status ?? 'empty'} />} />
        <SummaryCard title="Ist-Zeit" value={formatMinutes(selectedDayAccount.data?.actual_minutes ?? 0)} />
        <SummaryCard title="Pausen" value={formatMinutes(selectedDayAccount.data?.break_minutes ?? 0)} />
        <SummaryCard title="Balance" value={formatMinutes(selectedDayAccount.data?.balance_minutes ?? 0)} />
        <SummaryCard title="Abwesenheit" value={selectedAbsenceLabel} />
      </section>

      <section className="card my-time-calendar-section" style={{ marginTop: '1rem' }} aria-label="Monatskalender">
        <div className="actions" style={{ justifyContent: 'space-between' }}>
          <button
            className="btn outline"
            type="button"
            onClick={() => {
              setMonthCursor((prev) => {
                const date = new Date(prev.year, prev.month - 2, 1);
                return { year: date.getFullYear(), month: date.getMonth() + 1 };
              });
            }}
          >
            ← Monat zurück
          </button>
          <p className="meta" style={{ margin: 0 }} aria-live="polite">
            {monthCursor.month}.{monthCursor.year}
          </p>
          <button
            className="btn outline"
            type="button"
            onClick={() => {
              setMonthCursor((prev) => {
                const date = new Date(prev.year, prev.month, 1);
                return { year: date.getFullYear(), month: date.getMonth() + 1 };
              });
            }}
          >
            Monat vor →
          </button>
        </div>
        {calendar.data ? (
          <DashboardMonthCalendar
            year={calendar.data.year}
            month={calendar.data.month}
            days={calendar.data.days}
            selectedDate={selectedDate}
            onSelectDate={setSelectedDate}
            title="Monatskalender"
            subtitle="Tag auswählen, um Ereignisse direkt zu prüfen"
          />
        ) : null}
      </section>

      <DataSection title="Zeitereignisliste">
        <p className="meta">
          Einträge für <strong>{selectedDate}</strong>. <Link to={`/day?date=${selectedDate}`}>Tag öffnen</Link> für ausführliche Erfassung.
        </p>
        {!selectedDayEvents.data?.length ? (
          <EmptyState title="Keine Einträge für diesen Tag" description="Nutze Schnellerfassung oder öffne die Tagesansicht zur Nacherfassung." />
        ) : (
          <DataGrid columns={columns} data={selectedDayEvents.data} searchPlaceholder="Ereignisse durchsuchen…" />
        )}
      </DataSection>
    </>
  );
}
