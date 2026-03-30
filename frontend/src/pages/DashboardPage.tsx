import { PageHeader, SummaryCard, StatusBadge, ErrorState, LoadingBlock } from '../components/common';
import { useClockMutation, useCurrentStatus, useDailyAccount, useTimeStamps } from '../hooks/useZytlogApi';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

export function DashboardPage() {
  const today = isoDate(new Date());
  const currentStatus = useCurrentStatus();
  const dailyAccount = useDailyAccount(today);
  const events = useTimeStamps(today, today);
  const clockIn = useClockMutation('in');
  const clockOut = useClockMutation('out');

  if (currentStatus.isLoading || dailyAccount.isLoading || events.isLoading) return <LoadingBlock />;
  if (currentStatus.error || dailyAccount.error || events.error) return <ErrorState message="Could not load dashboard data." />;

  const status = currentStatus.data?.status ?? 'clocked_out';
  const lastEvent = events.data?.[events.data.length - 1];

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Current status and today overview" />
      <div className="grid">
        <SummaryCard title="Current Status" value={<StatusBadge status={status} />} hint={currentStatus.data?.last_event_timestamp ? `Last update: ${formatDateTime(currentStatus.data.last_event_timestamp)}` : 'No events yet'} />
        <SummaryCard title="Today Target" value={formatMinutes(dailyAccount.data?.target_minutes ?? 0)} />
        <SummaryCard title="Today Actual" value={formatMinutes(dailyAccount.data?.actual_minutes ?? 0)} />
        <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data?.balance_minutes ?? 0)} hint={<StatusBadge status={dailyAccount.data?.status ?? 'empty'} />} />
      </div>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h3>Actions</h3>
        <div className="actions">
          <button className="btn primary" onClick={() => clockIn.mutate()} disabled={status === 'clocked_in' || clockIn.isPending}>
            Clock In
          </button>
          <button className="btn outline" onClick={() => clockOut.mutate()} disabled={status === 'clocked_out' || clockOut.isPending}>
            Clock Out
          </button>
        </div>
        {lastEvent ? <p className="meta">Last event: {lastEvent.type} at {formatDateTime(lastEvent.timestamp)}</p> : null}
      </section>
    </>
  );
}
