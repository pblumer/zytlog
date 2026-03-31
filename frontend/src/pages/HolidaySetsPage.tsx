import { FormEvent, useMemo, useState } from 'react';

import { useAuth } from '../auth/provider';
import { ApiError } from '../api/client';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import { DataGrid } from '../components/DataGrid';
import type { DataGridColumn } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import {
  useCreateHolidaySetMutation,
  useDeleteHolidaySetMutation,
  useHolidaySets,
  useUpdateHolidaySetMutation,
} from '../hooks/useZytlogApi';
import type { HolidaySet } from '../types/api';

type HolidaySetFormState = {
  name: string;
  description: string;
  source: string;
  active: boolean;
};

const defaultFormState: HolidaySetFormState = {
  name: '',
  description: '',
  source: 'manual',
  active: true,
};

export function HolidaySetsPage() {
  const { isAdmin } = useAuth();
  const [editingHolidaySetId, setEditingHolidaySetId] = useState<number | null>(null);
  const [formState, setFormState] = useState<HolidaySetFormState>(defaultFormState);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const query = useHolidaySets(isAdmin);
  const createMutation = useCreateHolidaySetMutation();
  const updateMutation = useUpdateHolidaySetMutation();
  const deleteMutation = useDeleteHolidaySetMutation();

  const columns = useMemo<DataGridColumn<HolidaySet>[]>(
    () => [
      { id: 'name', header: 'Name', cell: (row) => row.name, searchableText: (row) => row.name, sortable: true },
      {
        id: 'description',
        header: 'Beschreibung',
        cell: (row) => row.description ?? '—',
        searchableText: (row) => row.description ?? '',
      },
      { id: 'source', header: 'Quelle', cell: (row) => row.source ?? 'manuell' },
      { id: 'holiday_count', header: 'Feiertage', cell: (row) => row.holiday_count, sortable: true, sortValue: (row) => row.holiday_count },
      { id: 'active', header: 'Aktiv', cell: (row) => <TableStatusBadge status={row.active ? 'complete' : 'empty'} /> },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => (
          <div className="actions">
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setEditingHolidaySetId(row.id);
                setFormState({
                  name: row.name,
                  description: row.description ?? '',
                  source: row.source ?? 'manual',
                  active: row.active,
                });
                setMutationError(null);
              }}
            >
              Feiertagssatz bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={async () => {
                if (!window.confirm(`Feiertagssatz „${row.name}“ löschen?`)) return;
                try {
                  await deleteMutation.mutateAsync(row.id);
                } catch (error) {
                  setMutationError(error instanceof Error ? error.message : 'Feiertagssatz konnte nicht gelöscht werden.');
                }
              }}
            >
              Feiertagssatz löschen
            </button>
          </div>
        ),
      },
    ],
    [deleteMutation],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMutationError(null);
    const payload = {
      name: formState.name,
      description: formState.description || null,
      source: formState.source || null,
      country_code: null,
      region_code: null,
      active: formState.active,
    };

    try {
      if (editingHolidaySetId != null) {
        await updateMutation.mutateAsync({ holidaySetId: editingHolidaySetId, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setEditingHolidaySetId(null);
      setFormState(defaultFormState);
    } catch (error) {
      if (error instanceof ApiError) {
        setMutationError(error.message);
        return;
      }
      setMutationError('Feiertagssatz konnte nicht gespeichert werden.');
    }
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Feiertagssätze sind nur für Administratoren sichtbar." />;
  }

  return (
    <>
      <PageHeader title="Feiertagssätze" subtitle="Wiederverwendbare Feiertagssätze pro Tenant verwalten" />
      <DataSection title={editingHolidaySetId ? 'Feiertagssatz bearbeiten' : 'Feiertagssatz anlegen'}>
        <form className="grid" onSubmit={onSubmit}>
          <label>
            Name
            <input value={formState.name} onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))} required />
          </label>
          <label>
            Beschreibung
            <input value={formState.description} onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))} />
          </label>
          <label>
            Quelle
            <input value={formState.source} onChange={(event) => setFormState((prev) => ({ ...prev, source: event.target.value }))} />
          </label>
          <label>
            <input type="checkbox" checked={formState.active} onChange={(event) => setFormState((prev) => ({ ...prev, active: event.target.checked }))} /> Aktiv
          </label>
          <div className="actions">
            <button type="submit" className="btn primary">{editingHolidaySetId ? 'Änderungen speichern' : 'Feiertagssatz speichern'}</button>
          </div>
          {mutationError ? <p className="inline-error">{mutationError}</p> : null}
        </form>
      </DataSection>
      <DataSection title="Feiertagssätze">
        {query.isLoading ? <LoadingBlock /> : null}
        {query.error ? <ErrorState message="Feiertagssätze konnten nicht geladen werden." /> : null}
        {query.data ? <DataGrid columns={columns} data={query.data} searchPlaceholder="Feiertagssätze suchen…" /> : null}
      </DataSection>
    </>
  );
}
