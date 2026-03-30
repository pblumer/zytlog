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

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Aktueller Status und heutige Übersicht" />
      <div className="grid">
        <SummaryCard title="Aktueller Status" value={<StatusBadge status={status} />} hint={currentStatus.data?.last_event_timestamp ? `Letzte Buchung: ${formatDateTime(currentStatus.data.last_event_timestamp)}` : 'Noch keine Buchung'} />
        <SummaryCard title="Soll heute" value={formatMinutes(dailyAccount.data?.target_minutes ?? 0)} />
        <SummaryCard title="Ist heute" value={formatMinutes(dailyAccount.data?.actual_minutes ?? 0)} />
        <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data?.balance_minutes ?? 0)} hint={<StatusBadge status={dailyAccount.data?.status ?? 'empty'} />} />
      </div>

      <QuickStampCard status={status} lastEventTimestamp={lastEvent?.timestamp ?? currentStatus.data?.last_event_timestamp} />

      {calendar.data ? <DashboardMonthCalendar year={calendar.data.year} month={calendar.data.month} days={calendar.data.days} /> : null}
    </>
  );
}
