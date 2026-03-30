import { useMemo } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useAuth } from '../auth/provider';
import { useWorkingTimeModels } from '../hooks/useZytlogApi';
import type { WorkingTimeModel } from '../types/api';

export function WorkingTimeModelsPage() {
  const { isAdmin } = useAuth();
  const query = useWorkingTimeModels(isAdmin);

  const columns = useMemo<DataGridColumn<WorkingTimeModel>[]>(
    () => [
      { id: 'name', header: 'Name', cell: (row) => row.name, sortValue: (row) => row.name, searchableText: (row) => row.name, sortable: true },
      { id: 'weekly', header: 'Weekly Hours', cell: (row) => row.weekly_target_hours, sortValue: (row) => row.weekly_target_hours, sortable: true },
      { id: 'workdays', header: 'Workdays', cell: (row) => row.workdays_per_week, sortValue: (row) => row.workdays_per_week, sortable: true },
      {
        id: 'active',
        header: 'Status',
        cell: (row) => <TableStatusBadge status={row.active ? 'complete' : 'empty'} />,
        sortValue: (row) => (row.active ? 1 : 0),
        searchableText: (row) => (row.active ? 'active complete' : 'inactive empty'),
        sortable: true,
      },
    ],
    [],
  );

  if (!isAdmin) {
    return <EmptyState title="Not available" description="Working time models are restricted to administrators." />;
  }

  return (
    <>
      <PageHeader title="Working Time Models" subtitle="Read-only list for this stage" />
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load models." /> : null}
      {query.data ? (
        <DataSection title="Models">
          <DataGrid columns={columns} data={query.data} searchPlaceholder="Search models…" />
        </DataSection>
      ) : null}
    </>
  );
}
