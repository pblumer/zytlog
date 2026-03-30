import { useState } from 'react';

import { DataSection, ErrorState, LoadingBlock, PageHeader, StatusBadge, SummaryCard } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useMonthReport } from '../hooks/useZytlogApi';
import type { DailyOverviewRow } from '../types/api';
import { formatMinutes } from '../utils/date';

const now = new Date();

export function MonthPage() {
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const query = useMonthReport(year, month);

  return (
    <>
      <PageHeader
        title="Month"
        subtitle="Monthly overview"
        actions={
          <>
            <input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} min={1970} max={2100} />
            <input type="number" value={month} onChange={(event) => setMonth(Number(event.target.value))} min={1} max={12} />
          </>
        }
      />
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load monthly report." /> : null}
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
