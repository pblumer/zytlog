import { useState } from 'react';

import { DataSection, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useYearReport } from '../hooks/useZytlogApi';
import type { MonthlySummaryRow } from '../types/api';
import { formatMinutes } from '../utils/date';

const now = new Date();

export function YearPage() {
  const [year, setYear] = useState(now.getFullYear());
  const query = useYearReport(year);

  return (
    <>
      <PageHeader
        title="Year"
        subtitle="Yearly totals"
        actions={<input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} min={1970} max={2100} />}
      />
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load yearly report." /> : null}
      {query.data ? (
        <>
          <div className="grid">
            <SummaryCard title="Target" value={formatMinutes(query.data.totals.target_minutes)} />
            <SummaryCard title="Actual" value={formatMinutes(query.data.totals.actual_minutes)} />
            <SummaryCard title="Balance" value={formatMinutes(query.data.totals.balance_minutes)} />
            <SummaryCard title="Days" value={query.data.totals.days_total} />
          </div>
          <DataSection title="Monthly Summary">
            <SimpleTable<MonthlySummaryRow>
              columns={[
                { key: 'month', header: 'Month', render: (row) => row.month },
                { key: 'target', header: 'Target', render: (row) => formatMinutes(row.target_minutes) },
                { key: 'actual', header: 'Actual', render: (row) => formatMinutes(row.actual_minutes) },
                { key: 'balance', header: 'Balance', render: (row) => formatMinutes(row.balance_minutes) },
                { key: 'days', header: 'Days', render: (row) => row.days_total },
              ]}
              data={query.data.months}
              rowKey={(row) => row.month.toString()}
            />
          </DataSection>
        </>
      ) : null}
    </>
  );
}
