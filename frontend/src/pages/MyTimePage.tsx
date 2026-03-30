import { useMemo } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
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

  const columns = useMemo<DataGridColumn<TimeStampEvent>[]>(
    () => [
      { id: 'type', header: 'Type', cell: (row) => <TableStatusBadge status={row.type} />, sortValue: (row) => row.type, searchableText: (row) => row.type, sortable: true },
      { id: 'timestamp', header: 'Timestamp', cell: (row) => formatDateTime(row.timestamp), sortValue: (row) => row.timestamp, searchableText: (row) => row.timestamp, sortable: true },
      { id: 'source', header: 'Source', cell: (row) => row.source, sortValue: (row) => row.source, searchableText: (row) => row.source, sortable: true },
    ],
    [],
  );

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
        <SummaryCard title="Current" value={<TableStatusBadge status={currentStatus.data?.status ?? 'clocked_out'} />} />
        <SummaryCard title="Actual" value={formatMinutes(dailyAccount.data?.actual_minutes ?? 0)} />
        <SummaryCard title="Break" value={formatMinutes(dailyAccount.data?.break_minutes ?? 0)} />
        <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data?.balance_minutes ?? 0)} />
      </div>

      <DataSection title="Today's Events">
        {!events.data?.length ? (
          <EmptyState title="No events yet today" description="Use Clock In to start tracking your day." />
        ) : (
          <DataGrid columns={columns} data={events.data} searchPlaceholder="Search today's events…" />
        )}
      </DataSection>
    </>
  );
}
