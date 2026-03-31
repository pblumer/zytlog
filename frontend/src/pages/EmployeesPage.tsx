import { FormEvent, useMemo, useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { useAuth } from '../auth/provider';
import { useCreateEmployeeMutation, useEmployees, useWorkingTimeModels } from '../hooks/useZytlogApi';
import type { Employee } from '../types/api';

const weekdays = [
  { key: 'workday_monday', label: 'Mo' },
  { key: 'workday_tuesday', label: 'Di' },
  { key: 'workday_wednesday', label: 'Mi' },
  { key: 'workday_thursday', label: 'Do' },
  { key: 'workday_friday', label: 'Fr' },
  { key: 'workday_saturday', label: 'Sa' },
  { key: 'workday_sunday', label: 'So' },
] as const;

type WeekdayKey = (typeof weekdays)[number]['key'];

function formatOverridePattern(employee: Employee) {
  const hasOverride = weekdays.some((weekday) => employee[weekday.key] !== null);
  if (!hasOverride) return 'Standard-Arbeitstage';

  return (
    weekdays
      .filter((weekday) => employee[weekday.key] === true)
      .map((weekday) => weekday.label)
      .join(', ') || 'Kein Arbeitstag'
  );
}

export function EmployeesPage() {
  const { isAdmin } = useAuth();
  const query = useEmployees(isAdmin);
  const modelsQuery = useWorkingTimeModels(isAdmin);
  const createMutation = useCreateEmployeeMutation();

  const [userId, setUserId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [entryDate, setEntryDate] = useState('2026-01-01');
  const [employmentPercentage, setEmploymentPercentage] = useState('100');
  const [workingTimeModelId, setWorkingTimeModelId] = useState('');
  const [overridesEnabled, setOverridesEnabled] = useState(false);
  const [overrideValues, setOverrideValues] = useState<Record<WeekdayKey, boolean>>({
    workday_monday: true,
    workday_tuesday: true,
    workday_wednesday: true,
    workday_thursday: true,
    workday_friday: true,
    workday_saturday: false,
    workday_sunday: false,
  });

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
        header: 'Mitarbeiternr.',
        cell: (row) => row.employee_number ?? '—',
        sortValue: (row) => row.employee_number ?? '',
        searchableText: (row) => row.employee_number ?? '',
        sortable: true,
      },
      {
        id: 'employment',
        header: 'Arbeitspensum',
        cell: (row) => `${row.employment_percentage}%`,
        sortValue: (row) => row.employment_percentage,
        sortable: true,
      },
      {
        id: 'days',
        header: 'Individuelle Arbeitstage',
        cell: (row) => formatOverridePattern(row),
        searchableText: (row) => formatOverridePattern(row),
      },
    ],
    [],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await createMutation.mutateAsync({
      user_id: Number(userId),
      employee_number: null,
      first_name: firstName,
      last_name: lastName,
      employment_percentage: Number(employmentPercentage),
      entry_date: entryDate,
      exit_date: null,
      working_time_model_id: workingTimeModelId ? Number(workingTimeModelId) : null,
      workday_monday: overridesEnabled ? overrideValues.workday_monday : null,
      workday_tuesday: overridesEnabled ? overrideValues.workday_tuesday : null,
      workday_wednesday: overridesEnabled ? overrideValues.workday_wednesday : null,
      workday_thursday: overridesEnabled ? overrideValues.workday_thursday : null,
      workday_friday: overridesEnabled ? overrideValues.workday_friday : null,
      workday_saturday: overridesEnabled ? overrideValues.workday_saturday : null,
      workday_sunday: overridesEnabled ? overrideValues.workday_sunday : null,
      team: null,
    });
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Mitarbeiterverwaltung ist nur für Administratoren sichtbar." />;
  }

  return (
    <>
      <PageHeader title="Mitarbeiter" subtitle="Arbeitspensum und optionale individuelle Arbeitstage pro Mitarbeiter" />
      <DataSection title="Mitarbeiter anlegen">
        <form className="grid" onSubmit={onSubmit}>
          <label>
            User-ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} type="number" min="1" required />
          </label>
          <label>
            Vorname
            <input value={firstName} onChange={(event) => setFirstName(event.target.value)} required />
          </label>
          <label>
            Nachname
            <input value={lastName} onChange={(event) => setLastName(event.target.value)} required />
          </label>
          <label>
            Arbeitspensum (%)
            <input
              value={employmentPercentage}
              onChange={(event) => setEmploymentPercentage(event.target.value)}
              type="number"
              min="0"
              max="100"
              step="0.1"
              required
            />
          </label>
          <label>
            Eintrittsdatum
            <input value={entryDate} onChange={(event) => setEntryDate(event.target.value)} type="date" required />
          </label>
          <label>
            Arbeitszeitmodell
            <select value={workingTimeModelId} onChange={(event) => setWorkingTimeModelId(event.target.value)} required>
              <option value="">Bitte wählen</option>
              {(modelsQuery.data ?? []).map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={overridesEnabled}
              onChange={(event) => setOverridesEnabled(event.target.checked)}
            />{' '}
            Modell überschreiben
          </label>
          {overridesEnabled ? (
            <div>
              <strong>Individuelle Arbeitstage</strong>
              <div className="actions">
                {weekdays.map((weekday) => (
                  <label key={weekday.key}>
                    <input
                      type="checkbox"
                      checked={overrideValues[weekday.key]}
                      onChange={(event) => setOverrideValues((prev) => ({ ...prev, [weekday.key]: event.target.checked }))}
                    />{' '}
                    {weekday.label}
                  </label>
                ))}
              </div>
            </div>
          ) : null}
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            Mitarbeiter speichern
          </button>
          {createMutation.error ? <p className="inline-error">Mitarbeiter konnte nicht gespeichert werden.</p> : null}
        </form>
      </DataSection>
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Mitarbeiter konnten nicht geladen werden." /> : null}
      {query.data ? (
        <DataSection title="Mitarbeiter">
          <DataGrid columns={columns} data={query.data} searchPlaceholder="Mitarbeiter suchen…" />
        </DataSection>
      ) : null}
    </>
  );
}
