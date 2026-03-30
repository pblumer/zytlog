import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import { SimpleTable } from '../components/SimpleTable';
import { useAuth } from '../auth/provider';
import { useEmployees } from '../hooks/useZytlogApi';
import type { Employee } from '../types/api';

export function EmployeesPage() {
  const { isAdmin } = useAuth();
  const query = useEmployees(isAdmin);

  if (!isAdmin) {
    return <EmptyState title="Not available" description="Employee list is restricted to administrators." />;
  }

  return (
    <>
      <PageHeader title="Employees" subtitle="Tenant employee directory" />
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Could not load employees." /> : null}
      {query.data ? (
        <DataSection title="Employees">
          <SimpleTable<Employee>
            columns={[
              { key: 'name', header: 'Name', render: (row) => `${row.first_name} ${row.last_name}` },
              { key: 'employee_number', header: 'Employee #', render: (row) => row.employee_number ?? '—' },
              { key: 'team', header: 'Team', render: (row) => row.team ?? '—' },
              { key: 'employment', header: 'Employment %', render: (row) => row.employment_percentage },
            ]}
            data={query.data}
            rowKey={(row) => row.id.toString()}
          />
        </DataSection>
      ) : null}
    </>
  );
}
