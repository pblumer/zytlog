import { FormEvent, useMemo, useState } from 'react';

import { useAuth } from '../auth/provider';
import { ApiError } from '../api/client';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import {
  useCreateHolidayMutation,
  useDeleteHolidayMutation,
  useHolidays,
  useHolidaySets,
  useUpdateHolidayMutation,
} from '../hooks/useZytlogApi';
import type { Holiday } from '../types/api';

type HolidayFormState = {
  date: string;
  name: string;
  active: boolean;
};

const currentYear = new Date().getFullYear();

const defaultFormState: HolidayFormState = {
  date: `${currentYear}-01-01`,
  name: '',
  active: true,
};

export function HolidaysPage() {
  const { isAdmin } = useAuth();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [selectedHolidaySetId, setSelectedHolidaySetId] = useState<number | null>(null);
  const [editingHolidayId, setEditingHolidayId] = useState<number | null>(null);
  const [formState, setFormState] = useState<HolidayFormState>(defaultFormState);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const holidaySetsQuery = useHolidaySets(isAdmin);
  const query = useHolidays(isAdmin && selectedHolidaySetId !== null, selectedYear, selectedHolidaySetId ?? undefined);
  const createMutation = useCreateHolidayMutation();
  const updateMutation = useUpdateHolidayMutation();
  const deleteMutation = useDeleteHolidayMutation();

  const selectedHolidaySet = (holidaySetsQuery.data ?? []).find((item) => item.id === selectedHolidaySetId);

  const columns = useMemo<DataGridColumn<Holiday>[]>(
    () => [
      {
        id: 'date',
        header: 'Datum',
        cell: (row) => row.date,
        sortValue: (row) => row.date,
        searchableText: (row) => row.date,
        sortable: true,
      },
      {
        id: 'name',
        header: 'Name',
        cell: (row) => row.name,
        sortValue: (row) => row.name,
        searchableText: (row) => row.name,
        sortable: true,
      },
      {
        id: 'active',
        header: 'Aktiv',
        cell: (row) => <TableStatusBadge status={row.active ? 'complete' : 'empty'} />,
        sortValue: (row) => (row.active ? 1 : 0),
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
                setEditingHolidayId(row.id);
                setFormState({ date: row.date, name: row.name, active: row.active });
                setMutationError(null);
              }}
            >
              Feiertag bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={async () => {
                if (!window.confirm(`Feiertag „${row.name}“ löschen?`)) return;
                setMutationError(null);
                try {
                  await deleteMutation.mutateAsync(row.id);
                  if (editingHolidayId === row.id) {
                    setEditingHolidayId(null);
                    setFormState(defaultFormState);
                  }
                } catch (error) {
                  setMutationError(error instanceof Error ? error.message : 'Feiertag konnte nicht gelöscht werden.');
                }
              }}
            >
              Feiertag löschen
            </button>
          </div>
        ),
      },
    ],
    [deleteMutation, editingHolidayId],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (selectedHolidaySetId === null) {
      setMutationError('Bitte zuerst einen Feiertagssatz auswählen.');
      return;
    }
    setMutationError(null);

    const payload = { ...formState, holiday_set_id: selectedHolidaySetId };

    try {
      if (editingHolidayId != null) {
        await updateMutation.mutateAsync({ holidayId: editingHolidayId, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setEditingHolidayId(null);
      setFormState(defaultFormState);
    } catch (error) {
      if (error instanceof ApiError) {
        setMutationError(error.message);
        return;
      }
      setMutationError('Feiertag konnte nicht gespeichert werden.');
    }
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Feiertage sind nur für Administratoren sichtbar." />;
  }

  return (
    <>
      <PageHeader title="Feiertage" subtitle="Feiertage innerhalb eines Feiertagssatzes verwalten" />
      <DataSection title="Feiertagssatz auswählen">
        <label>
          Feiertagssatz
          <select
            value={selectedHolidaySetId ?? ''}
            onChange={(event) => setSelectedHolidaySetId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">Bitte wählen</option>
            {(holidaySetsQuery.data ?? []).map((holidaySet) => (
              <option key={holidaySet.id} value={holidaySet.id}>
                {holidaySet.name}
              </option>
            ))}
          </select>
        </label>
        {selectedHolidaySet ? <p className="meta">Quelle: {selectedHolidaySet.source ?? 'manuell'}</p> : null}
      </DataSection>

      <DataSection title={editingHolidayId ? 'Feiertag bearbeiten' : 'Feiertag anlegen'}>
        <form className="app-form" onSubmit={onSubmit}>
          <label>
            Datum
            <input type="date" value={formState.date} onChange={(event) => setFormState((prev) => ({ ...prev, date: event.target.value }))} required />
          </label>
          <label>
            Name
            <input value={formState.name} onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))} required />
          </label>
          <label className="app-form-check">
            <input type="checkbox" checked={formState.active} onChange={(event) => setFormState((prev) => ({ ...prev, active: event.target.checked }))} /> Aktiv
          </label>
          <div className="actions">
            <button type="submit" className="btn primary">{editingHolidayId ? 'Änderungen speichern' : 'Feiertag speichern'}</button>
            {editingHolidayId ? (
              <button type="button" className="btn outline" onClick={() => { setEditingHolidayId(null); setFormState(defaultFormState); }}>
                Abbrechen
              </button>
            ) : null}
          </div>
          {mutationError ? <p className="inline-error">{mutationError}</p> : null}
        </form>
      </DataSection>

      <DataSection title="Feiertagsliste">
        <label>
          Jahr
          <input type="number" min={1970} max={2100} value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))} aria-label="Jahr filtern" />
        </label>
        {holidaySetsQuery.isLoading || query.isLoading ? <LoadingBlock /> : null}
        {holidaySetsQuery.error || query.error ? <ErrorState message="Feiertage konnten nicht geladen werden." /> : null}
        {selectedHolidaySetId === null ? <EmptyState title="Kein Feiertagssatz ausgewählt" description="Wählen Sie einen Feiertagssatz, um Feiertage zu verwalten." /> : null}
        {query.data ? <DataGrid columns={columns} data={query.data} rowId={(row) => row.id} searchPlaceholder="Feiertage suchen…" /> : null}
      </DataSection>
    </>
  );
}
