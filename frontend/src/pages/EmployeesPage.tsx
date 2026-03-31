import { FormEvent, useMemo, useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { useAuth } from '../auth/provider';
import {
  useCreateEmployeeMutation,
  useEmployees,
  useUpdateEmployeeMutation,
  useWorkingTimeModels,
} from '../hooks/useZytlogApi';
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

type EmployeeFormState = {
  userId: string;
  employeeNumber: string;
  firstName: string;
  lastName: string;
  team: string;
  entryDate: string;
  exitDate: string;
  employmentPercentage: string;
  workingTimeModelId: string;
  overridesEnabled: boolean;
  overrideValues: Record<WeekdayKey, boolean>;
};

const defaultOverrideValues: Record<WeekdayKey, boolean> = {
  workday_monday: true,
  workday_tuesday: true,
  workday_wednesday: true,
  workday_thursday: true,
  workday_friday: true,
  workday_saturday: false,
  workday_sunday: false,
};

const createInitialFormState = (): EmployeeFormState => ({
  userId: '',
  employeeNumber: '',
  firstName: '',
  lastName: '',
  team: '',
  entryDate: '2026-01-01',
  exitDate: '',
  employmentPercentage: '100',
  workingTimeModelId: '',
  overridesEnabled: false,
  overrideValues: defaultOverrideValues,
});

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

function createEditState(employee: Employee): EmployeeFormState {
  const hasOverride = weekdays.some((weekday) => employee[weekday.key] !== null);
  return {
    userId: String(employee.user_id),
    employeeNumber: employee.employee_number ?? '',
    firstName: employee.first_name,
    lastName: employee.last_name,
    team: employee.team ?? '',
    entryDate: employee.entry_date,
    exitDate: employee.exit_date ?? '',
    employmentPercentage: String(employee.employment_percentage),
    workingTimeModelId: employee.working_time_model_id ? String(employee.working_time_model_id) : '',
    overridesEnabled: hasOverride,
    overrideValues: {
      workday_monday: employee.workday_monday ?? true,
      workday_tuesday: employee.workday_tuesday ?? true,
      workday_wednesday: employee.workday_wednesday ?? true,
      workday_thursday: employee.workday_thursday ?? true,
      workday_friday: employee.workday_friday ?? true,
      workday_saturday: employee.workday_saturday ?? false,
      workday_sunday: employee.workday_sunday ?? false,
    },
  };
}

export function EmployeesPage() {
  const { isAdmin } = useAuth();
  const query = useEmployees(isAdmin);
  const modelsQuery = useWorkingTimeModels(isAdmin);
  const createMutation = useCreateEmployeeMutation();
  const updateMutation = useUpdateEmployeeMutation();

  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [form, setForm] = useState<EmployeeFormState>(() => createInitialFormState());

  const modelsById = useMemo(
    () => new Map((modelsQuery.data ?? []).map((model) => [model.id, model.name])),
    [modelsQuery.data],
  );

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
        header: 'MitarbeiterNr.',
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
        id: 'working_time_model',
        header: 'Arbeitszeitmodell',
        cell: (row) => (row.working_time_model_id ? modelsById.get(row.working_time_model_id) ?? `#${row.working_time_model_id}` : '—'),
        searchableText: (row) => (row.working_time_model_id ? modelsById.get(row.working_time_model_id) ?? '' : ''),
      },
      {
        id: 'days',
        header: 'Arbeitstage',
        cell: (row) => formatOverridePattern(row),
        searchableText: (row) => formatOverridePattern(row),
      },
      {
        id: 'actions',
        header: 'Aktion',
        cell: (row) => (
          <button
            type="button"
            className="btn outline"
            onClick={() => {
              setEditingEmployee(row);
              setForm(createEditState(row));
            }}
          >
            Bearbeiten
          </button>
        ),
      },
    ],
    [modelsById],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();

    const payload = {
      employee_number: form.employeeNumber || null,
      first_name: form.firstName,
      last_name: form.lastName,
      employment_percentage: Number(form.employmentPercentage),
      entry_date: form.entryDate,
      exit_date: form.exitDate || null,
      working_time_model_id: form.workingTimeModelId ? Number(form.workingTimeModelId) : null,
      workday_monday: form.overridesEnabled ? form.overrideValues.workday_monday : null,
      workday_tuesday: form.overridesEnabled ? form.overrideValues.workday_tuesday : null,
      workday_wednesday: form.overridesEnabled ? form.overrideValues.workday_wednesday : null,
      workday_thursday: form.overridesEnabled ? form.overrideValues.workday_thursday : null,
      workday_friday: form.overridesEnabled ? form.overrideValues.workday_friday : null,
      workday_saturday: form.overridesEnabled ? form.overrideValues.workday_saturday : null,
      workday_sunday: form.overridesEnabled ? form.overrideValues.workday_sunday : null,
      team: form.team || null,
    };

    if (editingEmployee) {
      await updateMutation.mutateAsync({ employeeId: editingEmployee.id, payload });
      setEditingEmployee(null);
      setForm(createInitialFormState());
      return;
    }

    await createMutation.mutateAsync({
      user_id: Number(form.userId),
      ...payload,
    });
    setForm(createInitialFormState());
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Mitarbeiterverwaltung ist nur für Administratoren sichtbar." />;
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <PageHeader title="Mitarbeiter" subtitle="Mitarbeiterprofile verwalten und Arbeitszeitvorgaben pflegen" />
      <DataSection title="Hinweis zur Benutzeranlage">
        <p className="meta">
          Neue Benutzer werden aktuell zuerst in Keycloak angelegt. Nach dem ersten Login wird der Benutzer in Zytlog
          automatisch erstellt. Anschliessend kann das Mitarbeiterprofil hier ergänzt oder bearbeitet werden.
        </p>
        <p className="meta" style={{ marginTop: '0.35rem' }}>
          Falls eine Person bereits in Keycloak existiert, aber hier noch nicht vollständig gepflegt ist, kann das
          Mitarbeiterprofil hier ergänzt werden.
        </p>
      </DataSection>
      <DataSection title={editingEmployee ? 'Mitarbeiter bearbeiten' : 'Mitarbeiter anlegen'}>
        <form className="grid" onSubmit={onSubmit}>
          {!editingEmployee ? (
            <label>
              User-ID
              <input
                value={form.userId}
                onChange={(event) => setForm((prev) => ({ ...prev, userId: event.target.value }))}
                type="number"
                min="1"
                required
              />
            </label>
          ) : null}
          <label>
            MitarbeiterNr.
            <input
              value={form.employeeNumber}
              onChange={(event) => setForm((prev) => ({ ...prev, employeeNumber: event.target.value }))}
            />
          </label>
          <label>
            Vorname
            <input value={form.firstName} onChange={(event) => setForm((prev) => ({ ...prev, firstName: event.target.value }))} required />
          </label>
          <label>
            Nachname
            <input value={form.lastName} onChange={(event) => setForm((prev) => ({ ...prev, lastName: event.target.value }))} required />
          </label>
          <label>
            Arbeitspensum
            <input
              value={form.employmentPercentage}
              onChange={(event) => setForm((prev) => ({ ...prev, employmentPercentage: event.target.value }))}
              type="number"
              min="0"
              max="100"
              step="0.1"
              required
            />
          </label>
          <label>
            Arbeitszeitmodell
            <select
              value={form.workingTimeModelId}
              onChange={(event) => setForm((prev) => ({ ...prev, workingTimeModelId: event.target.value }))}
              required
            >
              <option value="">Bitte wählen</option>
              {(modelsQuery.data ?? []).map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Eintrittsdatum
            <input value={form.entryDate} onChange={(event) => setForm((prev) => ({ ...prev, entryDate: event.target.value }))} type="date" required />
          </label>
          <label>
            Austrittsdatum
            <input value={form.exitDate} onChange={(event) => setForm((prev) => ({ ...prev, exitDate: event.target.value }))} type="date" />
          </label>
          <label>
            Team
            <input value={form.team} onChange={(event) => setForm((prev) => ({ ...prev, team: event.target.value }))} />
          </label>
          <label>
            <input
              type="checkbox"
              checked={form.overridesEnabled}
              onChange={(event) => setForm((prev) => ({ ...prev, overridesEnabled: event.target.checked }))}
            />{' '}
            Individuelle Arbeitstage
          </label>
          <div>
            <strong>{form.overridesEnabled ? 'Individuelle Arbeitstage' : 'Standard-Arbeitstage'}</strong>
            {form.overridesEnabled ? (
              <div className="actions" style={{ marginTop: '0.35rem' }}>
                {weekdays.map((weekday) => (
                  <label key={weekday.key}>
                    <input
                      type="checkbox"
                      checked={form.overrideValues[weekday.key]}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          overrideValues: { ...prev.overrideValues, [weekday.key]: event.target.checked },
                        }))
                      }
                    />{' '}
                    {weekday.label}
                  </label>
                ))}
              </div>
            ) : (
              <p className="meta" style={{ marginTop: '0.25rem' }}>
                Es gelten die Standard-Arbeitstage aus dem Arbeitszeitmodell.
              </p>
            )}
          </div>
          <div className="actions">
            <button type="submit" className="btn primary" disabled={isPending}>
              {editingEmployee ? 'Änderungen speichern' : 'Mitarbeiter speichern'}
            </button>
            {editingEmployee ? (
              <button
                type="button"
                className="btn outline"
                onClick={() => {
                  setEditingEmployee(null);
                  setForm(createInitialFormState());
                }}
              >
                Abbrechen
              </button>
            ) : null}
          </div>
          {createMutation.error || updateMutation.error ? (
            <p className="inline-error">Mitarbeiter konnte nicht gespeichert werden.</p>
          ) : null}
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
