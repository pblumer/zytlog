import { FormEvent, useMemo, useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useAuth } from '../auth/provider';
import { ApiError } from '../api/client';
import {
  useCreateWorkingTimeModelMutation,
  useDeleteWorkingTimeModelMutation,
  useUpdateWorkingTimeModelMutation,
  useWorkingTimeModels,
} from '../hooks/useZytlogApi';
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

type ModelFormState = {
  name: string;
  annualTargetHours: string;
  active: boolean;
  selectedWeekdays: Record<WeekdayKey, boolean>;
};

const defaultFormState: ModelFormState = {
  name: 'Standard 42h',
  annualTargetHours: '2080',
  active: true,
  selectedWeekdays: {
    default_workday_monday: true,
    default_workday_tuesday: true,
    default_workday_wednesday: true,
    default_workday_thursday: true,
    default_workday_friday: true,
    default_workday_saturday: false,
    default_workday_sunday: false,
  },
};

function mapModelToForm(model: WorkingTimeModel): ModelFormState {
  return {
    name: model.name,
    annualTargetHours: String(model.annual_target_hours),
    active: model.active,
    selectedWeekdays: {
      default_workday_monday: model.default_workday_monday,
      default_workday_tuesday: model.default_workday_tuesday,
      default_workday_wednesday: model.default_workday_wednesday,
      default_workday_thursday: model.default_workday_thursday,
      default_workday_friday: model.default_workday_friday,
      default_workday_saturday: model.default_workday_saturday,
      default_workday_sunday: model.default_workday_sunday,
    },
  };
}

function formatWeekdayPattern(model: WorkingTimeModel) {
  return (
    weekdays
      .filter((weekday) => model[weekday.key])
      .map((weekday) => weekday.label)
      .join(', ') || 'Kein Arbeitstag'
  );
}

export function WorkingTimeModelsPage() {
  const { isAdmin } = useAuth();
  const query = useWorkingTimeModels(isAdmin);
  const createMutation = useCreateWorkingTimeModelMutation();
  const updateMutation = useUpdateWorkingTimeModelMutation();
  const deleteMutation = useDeleteWorkingTimeModelMutation();

  const [formState, setFormState] = useState<ModelFormState>(defaultFormState);
  const [editingModelId, setEditingModelId] = useState<number | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const columns = useMemo<DataGridColumn<WorkingTimeModel>[]>(
    () => [
      {
        id: 'name',
        header: 'Modell',
        cell: (row) => row.name,
        sortValue: (row) => row.name,
        searchableText: (row) => row.name,
        sortable: true,
      },
      {
        id: 'annual',
        header: 'Jahresarbeitszeit',
        cell: (row) => row.annual_target_hours,
        sortValue: (row) => row.annual_target_hours,
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
        cell: (row) => (
          <div>
            <TableStatusBadge status={row.active ? 'complete' : 'empty'} />
            <div className="meta">{row.active ? 'Aktiv' : 'Inaktiv'}</div>
          </div>
        ),
        sortValue: (row) => (row.active ? 1 : 0),
        sortable: true,
      },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => (
          <div className="actions">
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setEditingModelId(row.id);
                setFormState(mapModelToForm(row));
                setMutationError(null);
              }}
            >
              Bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              disabled={deleteMutation.isPending}
              onClick={async () => {
                const shouldDelete = window.confirm(`Arbeitszeitmodell „${row.name}“ wirklich löschen?`);
                if (!shouldDelete) {
                  return;
                }
                setMutationError(null);
                try {
                  await deleteMutation.mutateAsync(row.id);
                  if (editingModelId === row.id) {
                    setEditingModelId(null);
                    setFormState(defaultFormState);
                  }
                } catch (error) {
                  if (error instanceof ApiError) {
                    setMutationError(error.message);
                    return;
                  }
                  setMutationError('Arbeitszeitmodell konnte nicht gelöscht werden.');
                }
              }}
            >
              Löschen
            </button>
          </div>
        ),
      },
    ],
    [deleteMutation, editingModelId],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMutationError(null);

    const payload = {
      name: formState.name,
      annual_target_hours: Number(formState.annualTargetHours),
      active: formState.active,
      ...formState.selectedWeekdays,
    };

    try {
      if (editingModelId != null) {
        await updateMutation.mutateAsync({ modelId: editingModelId, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setEditingModelId(null);
      setFormState(defaultFormState);
    } catch (error) {
      if (error instanceof ApiError) {
        setMutationError(error.message);
        return;
      }
      setMutationError('Arbeitszeitmodell konnte nicht gespeichert werden.');
    }
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Arbeitszeitmodelle sind nur für Administratoren sichtbar." />;
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <PageHeader title="Arbeitszeitmodelle" subtitle="Jahresarbeitszeit und Standard-Arbeitstage pro Modell" />
      <DataSection title={editingModelId ? 'Arbeitszeitmodell bearbeiten' : 'Modell anlegen'}>
        <form className="grid" onSubmit={onSubmit}>
          <label>
            Modellname
            <input value={formState.name} onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))} required />
          </label>
          <label>
            Jahresarbeitszeit
            <input
              value={formState.annualTargetHours}
              onChange={(event) => setFormState((prev) => ({ ...prev, annualTargetHours: event.target.value }))}
              type="number"
              min="1"
              step="0.1"
              required
            />
          </label>
          <p className="meta">Jahresarbeitszeit ist die führende Sollgrösse des Modells.</p>
          <label>
            <input
              checked={formState.active}
              onChange={(event) => setFormState((prev) => ({ ...prev, active: event.target.checked }))}
              type="checkbox"
            />{' '}
            Aktiv
          </label>
          <div>
            <strong>Standard-Arbeitstage</strong>
            <div className="actions">
              {weekdays.map((weekday) => (
                <label key={weekday.key}>
                  <input
                    type="checkbox"
                    checked={formState.selectedWeekdays[weekday.key]}
                    onChange={(event) =>
                      setFormState((prev) => ({
                        ...prev,
                        selectedWeekdays: { ...prev.selectedWeekdays, [weekday.key]: event.target.checked },
                      }))
                    }
                  />{' '}
                  {weekday.label}
                </label>
              ))}
            </div>
          </div>
          <div className="actions">
            <button type="submit" className="btn primary" disabled={isSaving}>
              {editingModelId ? 'Änderungen speichern' : 'Modell speichern'}
            </button>
            {editingModelId ? (
              <button
                type="button"
                className="btn outline"
                onClick={() => {
                  setEditingModelId(null);
                  setFormState(defaultFormState);
                  setMutationError(null);
                }}
              >
                Abbrechen
              </button>
            ) : null}
          </div>
          {mutationError ? <p className="inline-error">{mutationError.includes('zugeordnet') ? `${mutationError} Dieses Modell wird noch verwendet.` : mutationError}</p> : null}
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
