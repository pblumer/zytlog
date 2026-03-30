import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, StatusBadge } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useAuth } from '../auth/provider';
import { useWorkingTimeModels } from '../hooks/useZytlogApi';
import type { WorkingTimeModel } from '../types/api';

export function WorkingTimeModelsPage() {
  const { isAdmin } = useAuth();
  const query = useWorkingTimeModels(isAdmin);

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
          <SimpleTable<WorkingTimeModel>
            columns={[
              { key: 'name', header: 'Name', render: (row) => row.name },
              { key: 'weekly', header: 'Weekly Hours', render: (row) => row.weekly_target_hours },
              { key: 'workdays', header: 'Workdays', render: (row) => row.workdays_per_week },
              { key: 'active', header: 'Status', render: (row) => <StatusBadge status={row.active ? 'active' : 'inactive'} /> },
            ]}
            data={query.data}
            rowKey={(row) => row.id.toString()}
          />
        </DataSection>
      ) : null}
    </>
  );
}
