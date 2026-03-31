import { FormEvent, useMemo, useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useAuth } from '../auth/provider';
import { useCreateWorkingTimeModelMutation, useWorkingTimeModels } from '../hooks/useZytlogApi';
import type { WorkingTimeModel } from '../types/api';

const weekdays = [
  { key: 'default_workday_monday', label: 'Mo' },
  { key: 'default_workday_tuesday', label: 'Di' },
  { key: 'default_workday_wednesday', label: 'Mi' },
  { key: 'default_workday_thursday', label: 'Do' },
  { key: 'default_workday_friday', label: 'Fr' },
  { key: 'default_workday_saturday', label: 'Sa' },
  { key: 'default_workday_sunday', label: 'So' },
] as const;

type WeekdayKey = (typeof weekdays)[number]['key'];

function formatWeekdayPattern(model: WorkingTimeModel) {
  return weekdays
    .filter((weekday) => model[weekday.key])
    .map((weekday) => weekday.label)
    .join(', ') || 'Kein Arbeitstag';
}

export function WorkingTimeModelsPage() {
  const { isAdmin } = useAuth();
  const query = useWorkingTimeModels(isAdmin);
  const createMutation = useCreateWorkingTimeModelMutation();

  const [name, setName] = useState('Standard 42h');
  const [weeklyTargetHours, setWeeklyTargetHours] = useState('42');
  const [annualTargetHours, setAnnualTargetHours] = useState('');
  const [active, setActive] = useState(true);
  const [selectedWeekdays, setSelectedWeekdays] = useState<Record<WeekdayKey, boolean>>({
    default_workday_monday: true,
    default_workday_tuesday: true,
    default_workday_wednesday: true,
    default_workday_thursday: true,
    default_workday_friday: true,
    default_workday_saturday: false,
    default_workday_sunday: false,
  });

  const columns = useMemo<DataGridColumn<WorkingTimeModel>[]>(
    () => [
      { id: 'name', header: 'Modell', cell: (row) => row.name, sortValue: (row) => row.name, searchableText: (row) => row.name, sortable: true },
      { id: 'weekly', header: 'Wochenzielstunden', cell: (row) => row.weekly_target_hours, sortValue: (row) => row.weekly_target_hours, sortable: true },
      {
        id: 'annual',
        header: 'Jahresarbeitszeit',
        cell: (row) => row.annual_target_hours ?? '—',
        sortValue: (row) => row.annual_target_hours ?? 0,
        sortable: true,
      },
      {
        id: 'workdays',
        header: 'Standard-Arbeitstage',
        cell: (row) => formatWeekdayPattern(row),
        searchableText: (row) => formatWeekdayPattern(row),
      },
      {
        id: 'active',
        header: 'Status',
        cell: (row) => <TableStatusBadge status={row.active ? 'complete' : 'empty'} />,
        sortValue: (row) => (row.active ? 1 : 0),
        sortable: true,
      },
    ],
    [],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const countActive = Object.values(selectedWeekdays).filter(Boolean).length;
    await createMutation.mutateAsync({
      name,
      weekly_target_hours: Number(weeklyTargetHours),
      default_workdays_per_week: countActive,
      annual_target_hours: annualTargetHours.trim() ? Number(annualTargetHours) : null,
      active,
      ...selectedWeekdays,
    });
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Arbeitszeitmodelle sind nur für Administratoren sichtbar." />;
  }

  return (
    <>
      <PageHeader title="Arbeitszeitmodelle" subtitle="Wochenzielstunden, Jahresarbeitszeit und Standard-Arbeitstage pro Modell" />
      <DataSection title="Modell anlegen">
        <form className="grid" onSubmit={onSubmit}>
          <label>
            Modellname
            <input value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label>
            Wochenzielstunden
            <input value={weeklyTargetHours} onChange={(event) => setWeeklyTargetHours(event.target.value)} type="number" min="1" step="0.1" required />
          </label>
          <label>
            Jahresarbeitszeit (optional)
            <input value={annualTargetHours} onChange={(event) => setAnnualTargetHours(event.target.value)} type="number" min="1" step="0.1" />
          </label>
          <label>
            <input checked={active} onChange={(event) => setActive(event.target.checked)} type="checkbox" /> Aktiv
          </label>
          <div>
            <strong>Arbeitstage</strong>
            <div className="actions">
              {weekdays.map((weekday) => (
                <label key={weekday.key}>
                  <input
                    type="checkbox"
                    checked={selectedWeekdays[weekday.key]}
                    onChange={(event) => setSelectedWeekdays((prev) => ({ ...prev, [weekday.key]: event.target.checked }))}
                  />{' '}
                  {weekday.label}
                </label>
              ))}
            </div>
          </div>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            Modell speichern
          </button>
          {createMutation.error ? <p className="inline-error">Modell konnte nicht gespeichert werden.</p> : null}
        </form>
      </DataSection>
      {query.isLoading ? <LoadingBlock /> : null}
      {query.error ? <ErrorState message="Arbeitszeitmodelle konnten nicht geladen werden." /> : null}
      {query.data ? (
        <DataSection title="Modelle">
          <DataGrid columns={columns} data={query.data} searchPlaceholder="Arbeitszeitmodelle suchen…" />
        </DataSection>
      ) : null}
    </>
  );
}
