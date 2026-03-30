import { useState } from 'react';

import { DataSection, ErrorState, LoadingBlock, PageHeader, StatusBadge, SummaryCard } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useWeekReport } from '../hooks/useZytlogApi';
import type { DailyOverviewRow } from '../types/api';
import { formatMinutes, getIsoWeek } from '../utils/date';

const nowWeek = getIsoWeek(new Date());

export function WeekPage() {
  const [year, setYear] = useState(nowWeek.year);
  const [week, setWeek] = useState(nowWeek.week);
  const query = useWeekReport(year, week);

  return (
    <>
      <PageHeader
        title="Week"
        subtitle="Weekly overview"
        actions={
          <>
            <input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} min={1970} max={2100} />
            <input type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} min={1} max={53} />
          </>
        }
      />
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load weekly report." /> : null}
      {query.data ? (
        <>
          <div className="grid">
            <SummaryCard title="Target" value={formatMinutes(query.data.totals.target_minutes)} />
            <SummaryCard title="Actual" value={formatMinutes(query.data.totals.actual_minutes)} />
            <SummaryCard title="Balance" value={formatMinutes(query.data.totals.balance_minutes)} />
            <SummaryCard title="Days" value={query.data.totals.days_total} />
          </div>
          <DataSection title="Daily Rows">
            <SimpleTable<DailyOverviewRow>
              columns={[
                { key: 'date', header: 'Date', render: (row) => row.date },
                { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
                { key: 'target', header: 'Target', render: (row) => formatMinutes(row.target_minutes) },
                { key: 'actual', header: 'Actual', render: (row) => formatMinutes(row.actual_minutes) },
                { key: 'balance', header: 'Balance', render: (row) => formatMinutes(row.balance_minutes) },
              ]}
              data={query.data.days}
              rowKey={(row) => row.date}
            />
          </DataSection>
        </>
      ) : null}
    </>
  );
}
