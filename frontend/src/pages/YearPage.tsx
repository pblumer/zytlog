import { useMemo, useState } from 'react';

import { DataSection, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TotalsBar } from '../components/TotalsBar';
import { useYearReport } from '../hooks/useZytlogApi';
import type { MonthlySummaryRow } from '../types/api';
import { formatMinutes } from '../utils/date';

const now = new Date();

export function YearPage() {
  const [year, setYear] = useState(now.getFullYear());
  const query = useYearReport(year);

  const columns = useMemo<DataGridColumn<MonthlySummaryRow>[]>(
    () => [
      { id: 'month', header: 'Month', cell: (row) => row.month, sortValue: (row) => row.month, searchableText: (row) => `${row.month}`, sortable: true },
      { id: 'target', header: 'Target', cell: (row) => formatMinutes(row.target_minutes), sortValue: (row) => row.target_minutes, sortable: true },
      { id: 'actual', header: 'Actual', cell: (row) => formatMinutes(row.actual_minutes), sortValue: (row) => row.actual_minutes, sortable: true },
      { id: 'balance', header: 'Balance', cell: (row) => formatMinutes(row.balance_minutes), sortValue: (row) => row.balance_minutes, sortable: true },
      { id: 'days', header: 'Days', cell: (row) => row.days_total, sortValue: (row) => row.days_total, sortable: true },
    ],
    [],
  );

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
            <TotalsBar
              items={[
                { label: 'Complete', value: query.data.totals.days_complete },
                { label: 'Incomplete', value: query.data.totals.days_incomplete },
                { label: 'Invalid', value: query.data.totals.days_invalid },
                { label: 'Empty', value: query.data.totals.days_empty },
              ]}
            />
            <DataGrid columns={columns} data={query.data.months} searchPlaceholder="Search months…" />
          </DataSection>
        </>
      ) : null}
    </>
  );
}
