import { FormEvent, useMemo, useState } from 'react';

import { useAuth } from '../auth/provider';
import { ApiError } from '../api/client';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import { DataGrid } from '../components/DataGrid';
import type { DataGridColumn } from '../components/DataGrid';
import {
  useCreateNonWorkingPeriodMutation,
  useCreateNonWorkingPeriodSetMutation,
  useDeleteNonWorkingPeriodMutation,
  useDeleteNonWorkingPeriodSetMutation,
  useNonWorkingPeriods,
  useNonWorkingPeriodSets,
  useUpdateNonWorkingPeriodMutation,
  useUpdateNonWorkingPeriodSetMutation,
} from '../hooks/useZytlogApi';
import type { NonWorkingPeriod, NonWorkingPeriodSet } from '../types/api';

type SetForm = { name: string; description: string; active: boolean };
type PeriodForm = { start_date: string; end_date: string; name: string; category: string };

const defaultSetForm: SetForm = { name: '', description: '', active: true };
const defaultPeriodForm: PeriodForm = { start_date: '', end_date: '', name: '', category: 'school_break' };

export function NonWorkingPeriodSetsPage() {
  const { isAdmin } = useAuth();
  const [editingSetId, setEditingSetId] = useState<number | null>(null);
  const [selectedSetId, setSelectedSetId] = useState<number | null>(null);
  const [setForm, setSetForm] = useState<SetForm>(defaultSetForm);
  const [editingPeriodId, setEditingPeriodId] = useState<number | null>(null);
  const [periodForm, setPeriodForm] = useState<PeriodForm>(defaultPeriodForm);
  const [error, setError] = useState<string | null>(null);
  const [confirmDeleteSet, setConfirmDeleteSet] = useState<{id: number; name: string} | null>(null);
  const [confirmDeletePeriod, setConfirmDeletePeriod] = useState<{periodSetId: number; periodId: number; name: string} | null>(null);

  const setsQuery = useNonWorkingPeriodSets(isAdmin);
  const periodsQuery = useNonWorkingPeriods(selectedSetId, isAdmin && selectedSetId !== null);
  const createSet = useCreateNonWorkingPeriodSetMutation();
  const updateSet = useUpdateNonWorkingPeriodSetMutation();
  const deleteSet = useDeleteNonWorkingPeriodSetMutation();
  const createPeriod = useCreateNonWorkingPeriodMutation();
  const updatePeriod = useUpdateNonWorkingPeriodMutation();
  const deletePeriod = useDeleteNonWorkingPeriodMutation();

  const setColumns = useMemo<DataGridColumn<NonWorkingPeriodSet>[]>(
    () => [
      { id: 'name', header: 'Name', cell: (row) => row.name, sortable: true, searchableText: (row) => row.name },
      { id: 'description', header: 'Beschreibung', cell: (row) => row.description ?? '—' },
      { id: 'period_count', header: 'Zeiträume', cell: (row) => row.period_count, sortable: true, sortValue: (row) => row.period_count },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => (
          <div className="actions">
            <button type="button" className="btn outline" onClick={() => setSelectedSetId(row.id)}>Zeiträume</button>
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setEditingSetId(row.id);
                setSetForm({ name: row.name, description: row.description ?? '', active: row.active });
              }}
            >
              Bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={() => {
                setConfirmDeleteSet({ id: row.id, name: row.name });
              }}
            >
              Löschen
            </button>
          </div>
        ),
      },
    ],
    [deleteSet, selectedSetId],
  );

  const periodColumns = useMemo<DataGridColumn<NonWorkingPeriod>[]>(
    () => [
      { id: 'name', header: 'Label', cell: (row) => row.name, sortable: true, searchableText: (row) => row.name },
      { id: 'category', header: 'Kategorie', cell: (row) => row.category ?? '—' },
      { id: 'start', header: 'Von', cell: (row) => row.start_date, sortable: true, sortValue: (row) => row.start_date },
      { id: 'end', header: 'Bis', cell: (row) => row.end_date, sortable: true, sortValue: (row) => row.end_date },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => (
          <div className="actions">
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setEditingPeriodId(row.id);
                setPeriodForm({ start_date: row.start_date, end_date: row.end_date, name: row.name, category: row.category ?? '' });
              }}
            >
              Bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={() => {
                if (!selectedSetId) return;
                setConfirmDeletePeriod({ periodSetId: selectedSetId, periodId: row.id, name: row.name });
              }}
            >
              Löschen
            </button>
          </div>
        ),
      },
    ],
    [deletePeriod, selectedSetId],
  );

  const onSubmitSet = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const payload = { name: setForm.name, description: setForm.description || null, active: setForm.active };
    try {
      if (editingSetId) {
        await updateSet.mutateAsync({ periodSetId: editingSetId, payload });
      } else {
        await createSet.mutateAsync(payload);
      }
      setEditingSetId(null);
      setSetForm(defaultSetForm);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Set konnte nicht gespeichert werden.');
    }
  };

  const onSubmitPeriod = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedSetId) return;
    setError(null);
    const payload = { ...periodForm, category: periodForm.category || null };
    try {
      if (editingPeriodId) {
        await updatePeriod.mutateAsync({ periodSetId: selectedSetId, periodId: editingPeriodId, payload });
      } else {
        await createPeriod.mutateAsync({ periodSetId: selectedSetId, payload });
      }
      setEditingPeriodId(null);
      setPeriodForm(defaultPeriodForm);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Zeitraum konnte nicht gespeichert werden.');
    }
  };

  if (!isAdmin) return <EmptyState title="Nicht verfügbar" description="Nur Admins können Arbeitsfrei-Zeiträume verwalten." />;

  return (
    <>
      <PageHeader title="Arbeitsfreie Zeiträume" subtitle="Set-basierte Verwaltung von schulferienbedingten arbeitsfreien Zeiträumen" />

      <DataSection title={editingSetId ? 'Arbeitsfrei-Set bearbeiten' : 'Arbeitsfrei-Set anlegen'}>
        <form className="app-form" onSubmit={onSubmitSet}>
          <label>Name<input value={setForm.name} onChange={(e) => setSetForm((p) => ({ ...p, name: e.target.value }))} required /></label>
          <label>Beschreibung<input value={setForm.description} onChange={(e) => setSetForm((p) => ({ ...p, description: e.target.value }))} /></label>
          <label className="app-form-check"><input type="checkbox" checked={setForm.active} onChange={(e) => setSetForm((p) => ({ ...p, active: e.target.checked }))} /> Aktiv</label>
          <div className="actions"><button type="submit" className="btn primary">Speichern</button></div>
        </form>
      </DataSection>

      <DataSection title="Arbeitsfrei-Sets">
        {setsQuery.isLoading ? <LoadingBlock /> : null}
        {setsQuery.error ? <ErrorState message="Arbeitsfrei-Sets konnten nicht geladen werden." /> : null}
        {setsQuery.data ? <DataGrid columns={setColumns} data={setsQuery.data} searchPlaceholder="Arbeitsfrei-Set suchen…" /> : null}
      </DataSection>

      <DataSection title="Zeiträume pro Set">
        <label>
          Set auswählen
          <select value={selectedSetId ?? ''} onChange={(e) => setSelectedSetId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Bitte wählen</option>
            {(setsQuery.data ?? []).map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
          </select>
        </label>
        {selectedSetId ? (
          <>
            <form className="app-form" onSubmit={onSubmitPeriod}>
              <label>Von<input type="date" value={periodForm.start_date} onChange={(e) => setPeriodForm((p) => ({ ...p, start_date: e.target.value }))} required /></label>
              <label>Bis<input type="date" value={periodForm.end_date} onChange={(e) => setPeriodForm((p) => ({ ...p, end_date: e.target.value }))} required /></label>
              <label>Label<input value={periodForm.name} onChange={(e) => setPeriodForm((p) => ({ ...p, name: e.target.value }))} required /></label>
              <label>Kategorie<input value={periodForm.category} onChange={(e) => setPeriodForm((p) => ({ ...p, category: e.target.value }))} placeholder="school_break" /></label>
              <div className="actions"><button type="submit" className="btn primary">Zeitraum speichern</button></div>
            </form>
            {periodsQuery.isLoading ? <LoadingBlock /> : null}
            {periodsQuery.error ? <ErrorState message="Zeiträume konnten nicht geladen werden." /> : null}
            {periodsQuery.data ? <DataGrid columns={periodColumns} data={periodsQuery.data} searchPlaceholder="Zeitraum suchen…" /> : null}
          </>
        ) : (
          <EmptyState title="Kein Set ausgewählt" description="Bitte ein Arbeitsfrei-Set auswählen." />
        )}
        {error ? <p className="inline-error">{error}</p> : null}
      </DataSection>
      <ConfirmDialog
        open={confirmDeleteSet !== null}
        title="Löschen bestätigen"
        message={confirmDeleteSet ? `Arbeitsfrei-Set „${confirmDeleteSet.name}" löschen?` : ''}
        variant="danger"
        confirmLabel="Löschen"
        onConfirm={async () => {
          if (!confirmDeleteSet) return;
          try {
            await deleteSet.mutateAsync(confirmDeleteSet.id);
            if (selectedSetId === confirmDeleteSet.id) setSelectedSetId(null);
          } catch (e) {
            setError(e instanceof Error ? e.message : 'Set konnte nicht gelöscht werden.');
          }
          setConfirmDeleteSet(null);
        }}
        onCancel={() => setConfirmDeleteSet(null)}
      />
      <ConfirmDialog
        open={confirmDeletePeriod !== null}
        title="Löschen bestätigen"
        message={confirmDeletePeriod ? `Zeitraum „${confirmDeletePeriod.name}" löschen?` : ''}
        variant="danger"
        confirmLabel="Löschen"
        onConfirm={async () => {
          if (!confirmDeletePeriod) return;
          try {
            await deletePeriod.mutateAsync({ periodSetId: confirmDeletePeriod.periodSetId, periodId: confirmDeletePeriod.periodId });
          } catch (e) {
            setError(e instanceof Error ? e.message : 'Zeitraum konnte nicht gelöscht werden.');
          }
          setConfirmDeletePeriod(null);
        }}
        onCancel={() => setConfirmDeletePeriod(null)}
      />
    </>
  );
}
