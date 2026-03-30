import { useMemo, useState } from 'react';

import { DataSection, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { TotalsBar } from '../components/TotalsBar';
import { useWeekReport } from '../hooks/useZytlogApi';
import type { DailyOverviewRow } from '../types/api';
import { formatMinutes, getIsoWeek } from '../utils/date';

const nowWeek = getIsoWeek(new Date());

export function WeekPage() {
  const [year, setYear] = useState(nowWeek.year);
  const [week, setWeek] = useState(nowWeek.week);
  const query = useWeekReport(year, week);

  const columns = useMemo<DataGridColumn<DailyOverviewRow>[]>(
    () => [
      { id: 'date', header: 'Date', cell: (row) => row.date, sortValue: (row) => row.date, searchableText: (row) => row.date, sortable: true },
      {
        id: 'status',
        header: 'Status',
        cell: (row) => <TableStatusBadge status={row.status} />,
        sortValue: (row) => row.status,
        searchableText: (row) => row.status,
        sortable: true,
      },
      { id: 'target', header: 'Target', cell: (row) => formatMinutes(row.target_minutes), sortValue: (row) => row.target_minutes, sortable: true },
      { id: 'actual', header: 'Actual', cell: (row) => formatMinutes(row.actual_minutes), sortValue: (row) => row.actual_minutes, sortable: true },
      { id: 'balance', header: 'Balance', cell: (row) => formatMinutes(row.balance_minutes), sortValue: (row) => row.balance_minutes, sortable: true },
    ],
    [],
  );

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
            <TotalsBar
              items={[
                { label: 'Complete', value: query.data.totals.days_complete },
                { label: 'Incomplete', value: query.data.totals.days_incomplete },
                { label: 'Invalid', value: query.data.totals.days_invalid },
                { label: 'Empty', value: query.data.totals.days_empty },
              ]}
            />
            <DataGrid columns={columns} data={query.data.days} searchPlaceholder="Search daily rows…" />
          </DataSection>
        </>
      ) : null}
    </>
  );
}
