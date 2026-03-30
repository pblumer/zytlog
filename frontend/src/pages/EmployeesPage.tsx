import { useMemo } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { useAuth } from '../auth/provider';
import { useEmployees } from '../hooks/useZytlogApi';
import type { Employee } from '../types/api';

export function EmployeesPage() {
  const { isAdmin } = useAuth();
  const query = useEmployees(isAdmin);

  const columns = useMemo<DataGridColumn<Employee>[]>(
    () => [
      {
        id: 'name',
        header: 'Name',
        cell: (row) => `${row.first_name} ${row.last_name}`,
        sortValue: (row) => `${row.last_name} ${row.first_name}`,
        searchableText: (row) => `${row.first_name} ${row.last_name}`,
        sortable: true,
      },
      {
        id: 'employee_number',
        header: 'Employee #',
        cell: (row) => row.employee_number ?? '—',
        sortValue: (row) => row.employee_number ?? '',
        searchableText: (row) => row.employee_number ?? '',
        sortable: true,
      },
      {
        id: 'team',
        header: 'Team',
        cell: (row) => row.team ?? '—',
        sortValue: (row) => row.team ?? '',
        searchableText: (row) => row.team ?? '',
        sortable: true,
      },
      {
        id: 'employment',
        header: 'Employment %',
        cell: (row) => `${row.employment_percentage}%`,
        sortValue: (row) => row.employment_percentage,
        sortable: true,
      },
    ],
    [],
  );

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
          <DataGrid columns={columns} data={query.data} searchPlaceholder="Search employees…" />
        </DataSection>
      ) : null}
    </>
  );
}
