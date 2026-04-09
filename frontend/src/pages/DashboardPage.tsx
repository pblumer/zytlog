import { useEffect, useState } from 'react';

import { DashboardMonthCalendar } from '../components/DashboardMonthCalendar';
import { EmptyState, ErrorState, LoadingBlock, PageHeader, StatusBadge, SummaryCard } from '../components/common';
import { QuickStampCard } from '../components/QuickStampCard';
import {
  useCurrentStatus,
  useDailyAccount,
  useDashboardCalendarMonth,
  useManualTimeStampMutation,
  useMonthReport,
  useTimeStamps,
} from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';
import { getSuggestedNextStampType } from '../utils/timeStampSuggestions';

function toInputDateTimeValue(value: Date) {
  return new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function toIsoOrNull(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function formatClockTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function DashboardPage() {
  const now = new Date();
  const today = isoDate(now);

  const currentStatus = useCurrentStatus();
  const dailyAccount = useDailyAccount(today);
  const events = useTimeStamps(today, today);
  const monthReport = useMonthReport(now.getFullYear(), now.getMonth() + 1);
  const calendar = useDashboardCalendarMonth(now.getFullYear(), now.getMonth() + 1);
  const manualMutation = useManualTimeStampMutation();

  const [manualType, setManualType] = useState<'clock_in' | 'clock_out'>('clock_in');
  const [manualTimestamp, setManualTimestamp] = useState(toInputDateTimeValue(new Date()));
  const [manualComment, setManualComment] = useState('');
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualSuccess, setManualSuccess] = useState<string | null>(null);
  const [manualDirty, setManualDirty] = useState(false);

  useEffect(() => {
    if (!manualSuccess) return;
    const timer = window.setTimeout(() => setManualSuccess(null), 2600);
    return () => window.clearTimeout(timer);
  }, [manualSuccess]);

  useEffect(() => {
    if (manualDirty) return;
    setManualType(getSuggestedNextStampType(events.data));
  }, [events.data, manualDirty]);

  if (currentStatus.isLoading || dailyAccount.isLoading || events.isLoading || monthReport.isLoading || calendar.isLoading) return <LoadingBlock />;
  if (currentStatus.error || dailyAccount.error || events.error || monthReport.error || calendar.error) return <ErrorState message="Could not load dashboard data." />;

  const status = currentStatus.data?.status ?? 'clocked_out';
  const todayTarget = dailyAccount.data?.target_minutes ?? 0;
  const todayActual = dailyAccount.data?.actual_minutes ?? 0;
  const todayBalance = dailyAccount.data?.balance_minutes ?? 0;
  const todayOpen = todayTarget - todayActual;

  const monthDaysToDate = (monthReport.data?.days ?? []).filter((day) => day.date <= today);
  const monthToDate = monthDaysToDate.reduce(
    (acc, day) => {
      acc.target += day.target_minutes;
      acc.actual += day.actual_minutes;
      return acc;
    },
    { target: 0, actual: 0 },
  );
  const monthOpen = monthToDate.target - monthToDate.actual;
  const monthBalance = monthToDate.actual - monthToDate.target;

  const todayEvents = [...(events.data ?? [])].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  const lastEvent = todayEvents[0];

  const guidance =
    status === 'clocked_in'
      ? 'Du bist aktuell eingestempelt. Nicht vergessen: beim Gehen ausstempeln.'
      : (dailyAccount.data?.status ?? 'empty') === 'incomplete'
        ? 'Heute ist noch unvollständig. Ergänze fehlende Stempel über die Nacherfassung.'
        : 'Alles bereit für die Zeiterfassung. Du kannst direkt stempeln oder nacherfassen.';

  const monthDays = monthReport.data?.days ?? [];
  const todayContext = monthDays.find((day) => day.date === today) ?? null;

  const monthContextCounts = monthDays.reduce(
    (acc, day) => {
      if (day.absence) acc.absences += 1;
      if (day.is_holiday) acc.holidays += 1;
      if (day.is_in_non_working_period) acc.nonWorking += 1;
      return acc;
    },
    { absences: 0, holidays: 0, nonWorking: 0 },
  );

  const calendarContextByDate = monthDays.reduce<Record<string, { holidayName?: string | null; nonWorkingLabel?: string | null }>>(
    (acc, day) => {
      if (day.holiday_name || day.non_working_period_label) {
        acc[day.date] = {
          holidayName: day.holiday_name,
          nonWorkingLabel: day.non_working_period_label,
        };
      }
      return acc;
    },
    {},
  );

  const submitManual = async () => {
    const parsed = toIsoOrNull(manualTimestamp);
    if (!parsed) {
      setManualError('Bitte gültiges Datum und Uhrzeit erfassen.');
      return;
    }
    if (manualComment.length > 300) {
      setManualError('Kommentar darf maximal 300 Zeichen enthalten.');
      return;
    }

    setManualError(null);
    setManualSuccess(null);
    try {
      await manualMutation.mutateAsync({
        type: manualType,
        timestamp: parsed,
        comment: manualComment.trim() || null,
      });
      setManualSuccess('Nacherfassung gespeichert.');
      setManualComment('');
      setManualTimestamp(toInputDateTimeValue(new Date()));
      setManualType(getSuggestedNextStampType(events.data));
      setManualDirty(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Nacherfassung fehlgeschlagen.';
      setManualError(message);
    }
  };

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Zeiterfassung im Fokus: Stempeln, Nacherfassung und klare Tages-/Monatszahlen" />

      <section className="dashboard-capture-layout" aria-label="Zeiterfassungsbereich">
        <div className="dashboard-capture-column">
          <QuickStampCard status={status} lastEventTimestamp={lastEvent?.timestamp ?? currentStatus.data?.last_event_timestamp} title="Stempeln" />

          <section className="card dashboard-manual-card" aria-label="Nacherfassung">
            <h3>Nacherfassung</h3>
            <p className="meta">Wenn du einen Stempel vergessen hast, kannst du ihn hier nachtragen (z.B. Kommen 08:15).</p>
            <form
              className="inline-form dashboard-manual-form"
              onSubmit={(event) => {
                event.preventDefault();
                void submitManual();
              }}
            >
              <div className="inline-form-row">
                <label htmlFor="dashboard-manual-type">Typ</label>
                <select
                  id="dashboard-manual-type"
                  value={manualType}
                  onChange={(event) => {
                    setManualType(event.target.value as 'clock_in' | 'clock_out');
                    setManualDirty(true);
                  }}
                >
                  <option value="clock_in">Kommen</option>
                  <option value="clock_out">Gehen</option>
                </select>
              </div>
              <div className="inline-form-row">
                <label htmlFor="dashboard-manual-time">Zeitpunkt</label>
                <input
                  id="dashboard-manual-time"
                  type="datetime-local"
                  required
                  value={manualTimestamp}
                  onChange={(event) => {
                    setManualTimestamp(event.target.value);
                    setManualDirty(true);
                  }}
                />
              </div>
              <div className="inline-form-row">
                <label htmlFor="dashboard-manual-comment">Kommentar (optional)</label>
                <input
                  id="dashboard-manual-comment"
                  type="text"
                  maxLength={300}
                  value={manualComment}
                  onChange={(event) => {
                    setManualComment(event.target.value);
                    setManualDirty(true);
                  }}
                />
              </div>
              <div className="actions">
                <button type="submit" className="btn primary" disabled={manualMutation.isPending}>
                  {manualMutation.isPending ? 'Speichere…' : 'Nacherfassung speichern'}
                </button>
              </div>
              {manualSuccess ? <p className="quick-stamp-success">{manualSuccess}</p> : null}
              {manualError ? <ErrorState message={manualError} /> : null}
            </form>
          </section>

          <section className="card dashboard-events-card" aria-label="Heutige Zeitereignisse">
            <h3>Heute erfasst</h3>
            {todayEvents.length ? (
              <ul className="dashboard-event-list">
                {todayEvents.slice(0, 6).map((event: TimeStampEvent) => (
                  <li key={event.id}>
                    <span className="time-value">{formatClockTime(event.timestamp)}</span>
                    <StatusBadge status={event.type} />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="Noch keine Stempel heute" description="Starte mit Kommen oder erfasse einen Zeitpunkt manuell." />
            )}
          </section>
        </div>

        <div className="dashboard-metrics-column">
          <section className="card">
            <h3>Heute</h3>
            <p className="meta">{guidance}</p>
            <div className="grid dashboard-kpi-grid">
              <SummaryCard title="Soll heute" value={<span className="time-value">{formatMinutes(todayTarget)}</span>} />
              <SummaryCard title="Ist heute" value={<span className="time-value">{formatMinutes(todayActual)}</span>} />
              <SummaryCard
                title="Offen heute"
                value={
                  <span className={`time-value ${todayOpen < 0 ? 'balance-positive' : todayOpen > 0 ? 'balance-negative' : 'balance-neutral'}`}>
                    {formatMinutes(todayOpen)}
                  </span>
                }
              />
              <SummaryCard
                title="Saldo heute"
                value={
                  <span className={`time-value ${todayBalance > 0 ? 'balance-positive' : todayBalance < 0 ? 'balance-negative' : 'balance-neutral'}`}>
                    {formatMinutes(todayBalance)}
                  </span>
                }
                hint={lastEvent?.timestamp ? `Letzte Buchung: ${formatDateTime(lastEvent.timestamp)}` : 'Noch keine Buchung'}
              />
            </div>
          </section>

          <section className="card">
            <h3>Monat bis heute</h3>
            <p className="meta">Stand {new Date().toLocaleDateString()}</p>
            <div className="grid dashboard-kpi-grid">
              <SummaryCard title="Soll Monat (bis heute)" value={<span className="time-value">{formatMinutes(monthToDate.target)}</span>} />
              <SummaryCard title="Ist Monat (bis heute)" value={<span className="time-value">{formatMinutes(monthToDate.actual)}</span>} />
              <SummaryCard
                title="Offen Monat"
                value={
                  <span className={`time-value ${monthOpen < 0 ? 'balance-positive' : monthOpen > 0 ? 'balance-negative' : 'balance-neutral'}`}>
                    {formatMinutes(monthOpen)}
                  </span>
                }
              />
              <SummaryCard
                title="Saldo bis heute"
                value={
                  <span className={`time-value ${monthBalance > 0 ? 'balance-positive' : monthBalance < 0 ? 'balance-negative' : 'balance-neutral'}`}>
                    {formatMinutes(monthBalance)}
                  </span>
                }
                hint={`Monatsziel total: ${formatMinutes(monthReport.data?.totals.target_minutes ?? 0)}`}
              />
            </div>
          </section>

          <section className="card dashboard-context-card" aria-label="Tageskontext">
            <h3>Kontext heute</h3>
            {todayContext?.absence || todayContext?.is_holiday || todayContext?.is_in_non_working_period ? (
              <div className="dashboard-context-chips">
                {todayContext?.absence ? (
                  <span className={`absence-badge absence-badge-${todayContext.absence.type}`}>{todayContext.absence.label}</span>
                ) : null}
                {todayContext?.is_holiday ? <span className="dashboard-context-chip dashboard-context-holiday">Feiertag: {todayContext.holiday_name}</span> : null}
                {todayContext?.is_in_non_working_period ? (
                  <span className="dashboard-context-chip dashboard-context-non-working">Arbeitsfrei: {todayContext.non_working_period_label}</span>
                ) : null}
              </div>
            ) : (
              <p className="meta">Keine Abwesenheit, kein Feiertag und kein arbeitsfreier Zeitraum für heute.</p>
            )}
          </section>
        </div>
      </section>

      {calendar.data ? (
        <section className="card dashboard-calendar-shell" aria-label="Monatskalender und Kontexte">
          <div className="dashboard-calendar-header">
            <h3>Monatsübersicht</h3>
            <p className="meta">Schneller Sprung in die Tagesansicht mit sichtbaren Kontexten (Abwesenheit, Feiertag, Arbeitsfrei).</p>
          </div>
          <div className="dashboard-context-summary">
            <SummaryCard title="Abwesenheitstage" value={monthContextCounts.absences} />
            <SummaryCard title="Feiertage" value={monthContextCounts.holidays} />
            <SummaryCard title="Arbeitsfreie Tage" value={monthContextCounts.nonWorking} />
          </div>
          <DashboardMonthCalendar
            embedded
            year={calendar.data.year}
            month={calendar.data.month}
            days={calendar.data.days}
            contextByDate={calendarContextByDate}
            title="Kalender"
            subtitle="Status + Kontexte pro Tag"
          />
        </section>
      ) : null}
    </>
  );
}
