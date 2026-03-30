import { DataSection, ErrorState, LoadingBlock, PageHeader, StatusBadge, SummaryCard } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useClockMutation, useCurrentStatus, useDailyAccount, useTimeStamps } from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

export function MyTimePage() {
  const today = isoDate(new Date());
  const currentStatus = useCurrentStatus();
  const dailyAccount = useDailyAccount(today);
  const events = useTimeStamps(today, today);
  const clockIn = useClockMutation('in');
  const clockOut = useClockMutation('out');

  if (currentStatus.isLoading || dailyAccount.isLoading || events.isLoading) return <LoadingBlock />;
  if (currentStatus.error || dailyAccount.error || events.error) return <ErrorState message="Could not load your time data." />;

  return (
    <>
      <PageHeader
        title="My Time"
        subtitle="Daily working page"
        actions={
          <>
            <button className="btn primary" onClick={() => clockIn.mutate()} disabled={currentStatus.data?.status === 'clocked_in' || clockIn.isPending}>
              Clock In
            </button>
            <button className="btn outline" onClick={() => clockOut.mutate()} disabled={currentStatus.data?.status === 'clocked_out' || clockOut.isPending}>
              Clock Out
            </button>
          </>
        }
      />
      <div className="grid">
        <SummaryCard title="Current" value={<StatusBadge status={currentStatus.data?.status ?? 'clocked_out'} />} />
        <SummaryCard title="Actual" value={formatMinutes(dailyAccount.data?.actual_minutes ?? 0)} />
        <SummaryCard title="Break" value={formatMinutes(dailyAccount.data?.break_minutes ?? 0)} />
        <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data?.balance_minutes ?? 0)} />
      </div>

      <DataSection title="Today's Events">
        <SimpleTable<TimeStampEvent>
          columns={[
            { key: 'type', header: 'Type', render: (event) => <StatusBadge status={event.type} /> },
            { key: 'time', header: 'Timestamp', render: (event) => formatDateTime(event.timestamp) },
            { key: 'source', header: 'Source', render: (event) => event.source },
          ]}
          data={events.data ?? []}
          rowKey={(event) => event.id.toString()}
        />
      </DataSection>
    </>
  );
}
