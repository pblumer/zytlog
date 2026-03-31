import { PageHeader, SummaryCard, StatusBadge, ErrorState, LoadingBlock } from '../components/common';
import { DashboardMonthCalendar } from '../components/DashboardMonthCalendar';
import { QuickStampCard } from '../components/QuickStampCard';
import { useCurrentStatus, useDailyAccount, useDashboardCalendarMonth, useTimeStamps } from '../hooks/useZytlogApi';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

export function DashboardPage() {
  const today = isoDate(new Date());
  const currentStatus = useCurrentStatus();
  const dailyAccount = useDailyAccount(today);
  const events = useTimeStamps(today, today);
  const now = new Date();
  const calendar = useDashboardCalendarMonth(now.getFullYear(), now.getMonth() + 1);

  if (currentStatus.isLoading || dailyAccount.isLoading || events.isLoading || calendar.isLoading) return <LoadingBlock />;
  if (currentStatus.error || dailyAccount.error || events.error || calendar.error) return <ErrorState message="Could not load dashboard data." />;

  const status = currentStatus.data?.status ?? 'clocked_out';
  const lastEvent = events.data?.[events.data.length - 1];
  const todayAbsence = dailyAccount.data?.absence;
  const todayAbsenceLabel = todayAbsence
    ? `${todayAbsence.label}${todayAbsence.duration_type === 'half_day_am' ? ' (AM)' : todayAbsence.duration_type === 'half_day_pm' ? ' (PM)' : ''}`
    : null;

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Aktueller Status und heutige Übersicht" />
      <section className="grid" aria-label="Heutige Kennzahlen">
        <SummaryCard title="Aktueller Status" value={<StatusBadge status={status} />} hint={currentStatus.data?.last_event_timestamp ? `Letzte Buchung: ${formatDateTime(currentStatus.data.last_event_timestamp)}` : 'Noch keine Buchung'} />
        <SummaryCard title="Soll heute" value={<span className="time-value">{formatMinutes(dailyAccount.data?.target_minutes ?? 0)}</span>} />
        <SummaryCard title="Ist heute" value={<span className="time-value">{formatMinutes(dailyAccount.data?.actual_minutes ?? 0)}</span>} />
        <SummaryCard
          title="Saldo heute"
          value={
            <span
              className={`time-value ${(dailyAccount.data?.balance_minutes ?? 0) > 0 ? 'balance-positive' : (dailyAccount.data?.balance_minutes ?? 0) < 0 ? 'balance-negative' : 'balance-neutral'}`}
            >
              {formatMinutes(dailyAccount.data?.balance_minutes ?? 0)}
            </span>
          }
          hint={<StatusBadge status={dailyAccount.data?.status ?? 'empty'} />}
        />
        {todayAbsenceLabel ? <SummaryCard title="Abwesenheit heute" value={todayAbsenceLabel} /> : null}
      </section>

      <QuickStampCard status={status} lastEventTimestamp={lastEvent?.timestamp ?? currentStatus.data?.last_event_timestamp} />

      {calendar.data ? <DashboardMonthCalendar year={calendar.data.year} month={calendar.data.month} days={calendar.data.days} /> : null}
    </>
  );
}
