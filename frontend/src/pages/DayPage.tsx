import { useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, StatusBadge, SummaryCard } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useDailyAccount, useTimeStamps } from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

export function DayPage() {
  const [date, setDate] = useState(isoDate(new Date()));
  const dailyAccount = useDailyAccount(date);
  const events = useTimeStamps(date, date);

  return (
    <>
      <PageHeader
        title="Day"
        subtitle="Inspect one day in detail"
        actions={<input type="date" value={date} onChange={(event) => setDate(event.target.value)} />}
      />

      {dailyAccount.isLoading || events.isLoading ? <LoadingBlock /> : null}
      {dailyAccount.error || events.error ? <ErrorState message="Could not load selected day." /> : null}

      {dailyAccount.data ? (
        <div className="grid">
          <SummaryCard title="Status" value={<StatusBadge status={dailyAccount.data.status} />} />
          <SummaryCard title="Target" value={formatMinutes(dailyAccount.data.target_minutes)} />
          <SummaryCard title="Actual" value={formatMinutes(dailyAccount.data.actual_minutes)} />
          <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data.balance_minutes)} />
        </div>
      ) : null}

      <DataSection title="Event List">
        {!events.data?.length ? (
          <EmptyState title="No events for this day" description="Time stamp events will appear here." />
        ) : (
          <SimpleTable<TimeStampEvent>
            columns={[
              { key: 'type', header: 'Type', render: (event) => <StatusBadge status={event.type} /> },
              { key: 'timestamp', header: 'Timestamp', render: (event) => formatDateTime(event.timestamp) },
              { key: 'comment', header: 'Comment', render: (event) => event.comment ?? '—' },
            ]}
            data={events.data}
            rowKey={(event) => event.id.toString()}
          />
        )}
      </DataSection>
    </>
  );
}
