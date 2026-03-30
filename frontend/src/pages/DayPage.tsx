import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { InlineEditActions } from '../components/InlineEditActions';
import { ReportExportActions } from '../components/ReportExportActions';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useReportExport } from '../hooks/useReportExport';
import {
  useDailyAccount,
  useDeleteTimeStampMutation,
  useManualTimeStampMutation,
  useTimeStamps,
  useUpdateTimeStampMutation,
} from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';
import { getSuggestedNextStampType } from '../utils/timeStampSuggestions';

type EditDraft = {
  timestamp: string;
  comment: string;
};

function toInputDateTimeValue(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function toIsoOrNull(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export function DayPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [date, setDate] = useState(searchParams.get('date') ?? isoDate(new Date()));
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualType, setManualType] = useState<'clock_in' | 'clock_out'>('clock_in');
  const [manualTimestamp, setManualTimestamp] = useState(`${searchParams.get('date') ?? isoDate(new Date())}T08:00`);
  const [manualComment, setManualComment] = useState('');
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualDirty, setManualDirty] = useState(false);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [draft, setDraft] = useState<EditDraft | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingRowId, setDeletingRowId] = useState<number | null>(null);

  const dailyAccount = useDailyAccount(date);
  const events = useTimeStamps(date, date);
  const updateMutation = useUpdateTimeStampMutation();
  const deleteMutation = useDeleteTimeStampMutation();
  const manualMutation = useManualTimeStampMutation();
  const exporter = useReportExport();

  const startEdit = (event: TimeStampEvent) => {
    setEditingRowId(event.id);
    setDraft({
      timestamp: toInputDateTimeValue(event.timestamp),
      comment: event.comment ?? '',
    });
    setEditError(null);
  };

  const cancelEdit = () => {
    setEditingRowId(null);
    setDraft(null);
    setEditError(null);
  };

  const saveEdit = async (eventId: number) => {
    if (!draft) return;
    const parsedTimestamp = toIsoOrNull(draft.timestamp);
    if (!parsedTimestamp) {
      setEditError('Timestamp is required and must be valid.');
      return;
    }
    if (draft.comment.length > 300) {
      setEditError('Comment must be at most 300 characters.');
      return;
    }

    setEditError(null);
    try {
      await updateMutation.mutateAsync({
        eventId,
        timestamp: parsedTimestamp,
        comment: draft.comment.trim() || null,
      });
      cancelEdit();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not save correction. Please retry.';
      setEditError(message);
    }
  };

  const deleteEvent = async (event: TimeStampEvent) => {
    const confirmed = window.confirm('Wirklich löschen?');
    if (!confirmed) return;

    setDeleteError(null);
    setDeletingRowId(event.id);
    try {
      await deleteMutation.mutateAsync(event.id);
      if (editingRowId === event.id) {
        cancelEdit();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Löschen fehlgeschlagen.';
      setDeleteError(message);
    } finally {
      setDeletingRowId(null);
    }
  };

  const columns = useMemo<DataGridColumn<TimeStampEvent>[]>(
    () => [
      {
        id: 'type',
        header: 'Typ',
        cell: (row) => <TableStatusBadge status={row.type} />,
        sortValue: (row) => row.type,
        searchableText: (row) => row.type,
        sortable: true,
      },
      {
        id: 'timestamp',
        header: 'Zeitpunkt',
        cell: (row) => {
          if (editingRowId === row.id && draft) {
            return (
              <input
                type="datetime-local"
                value={draft.timestamp}
                onChange={(event) => setDraft((prev) => (prev ? { ...prev, timestamp: event.target.value } : prev))}
              />
            );
          }
          return formatDateTime(row.timestamp);
        },
        sortValue: (row) => row.timestamp,
        searchableText: (row) => row.timestamp,
        sortable: true,
      },
      {
        id: 'comment',
        header: 'Kommentar',
        cell: (row) => {
          if (editingRowId === row.id && draft) {
            return (
              <input
                type="text"
                value={draft.comment}
                maxLength={300}
                onChange={(event) => setDraft((prev) => (prev ? { ...prev, comment: event.target.value } : prev))}
              />
            );
          }
          return row.comment ?? '—';
        },
        searchableText: (row) => row.comment ?? '',
      },
      {
        id: 'corrected',
        header: 'Korrigiert',
        cell: (row) => (new Date(row.updated_at).getTime() > new Date(row.created_at).getTime() ? 'Ja' : 'Nein'),
        sortValue: (row) => row.updated_at,
        searchableText: (row) => row.updated_at,
        sortable: true,
      },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => {
          if (editingRowId === row.id) {
            return (
              <InlineEditActions
                onSave={() => {
                  void saveEdit(row.id);
                }}
                onCancel={cancelEdit}
                saveDisabled={updateMutation.isPending}
                saving={updateMutation.isPending}
              />
            );
          }

          return (
            <div className="actions">
              <button type="button" className="btn outline" onClick={() => startEdit(row)} disabled={deletingRowId === row.id}>
                Bearbeiten
              </button>
              <button
                type="button"
                className="btn danger"
                onClick={() => {
                  void deleteEvent(row);
                }}
                disabled={deletingRowId === row.id || deleteMutation.isPending}
              >
                {deletingRowId === row.id ? 'Lösche…' : 'Löschen'}
              </button>
            </div>
          );
        },
      },
    ],
    [deleteMutation.isPending, deletingRowId, draft, editingRowId, updateMutation.isPending],
  );

  const resetManualForm = () => {
    setShowManualForm(false);
    setManualType(getSuggestedNextStampType(events.data));
    setManualTimestamp(`${date}T08:00`);
    setManualComment('');
    setManualError(null);
    setManualDirty(false);
  };

  useEffect(() => {
    if (!showManualForm || manualDirty) return;
    setManualType(getSuggestedNextStampType(events.data));
  }, [events.data, manualDirty, showManualForm]);

  const submitManualForm = async () => {
    const parsed = toIsoOrNull(manualTimestamp);
    if (!parsed) {
      setManualError('Zeitpunkt ist erforderlich.');
      return;
    }

    setManualError(null);
    try {
      await manualMutation.mutateAsync({
        type: manualType,
        timestamp: parsed,
        comment: manualComment.trim() || null,
      });
      resetManualForm();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Eintrag konnte nicht gespeichert werden.';
      setManualError(message);
    }
  };

  return (
    <>
      <PageHeader
        title="Tag"
        subtitle="Detaillierte Tagesansicht"
        actions={
          <>
            <input
              type="date"
              value={date}
              onChange={(event) => {
                const value = event.target.value;
                setDate(value);
                setSearchParams({ date: value });
                setManualTimestamp(`${value}T08:00`);
                if (showManualForm && !manualDirty) {
                  setManualType(getSuggestedNextStampType(events.data));
                }
                exporter.clearError();
              }}
            />
            <ReportExportActions disabled={exporter.isExporting} onExport={(format) => void exporter.exportDay(date, format)} />
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setShowManualForm((prev) => {
                  const next = !prev;
                  if (next) {
                    setManualType(getSuggestedNextStampType(events.data));
                    setManualTimestamp(`${date}T08:00`);
                    setManualComment('');
                    setManualDirty(false);
                    setManualError(null);
                  }
                  return next;
                });
              }}
            >
              Zeitstempel nacherfassen
            </button>
          </>
        }
      />

      {exporter.error ? <ErrorState message={exporter.error} /> : null}
      {dailyAccount.isLoading || events.isLoading ? <LoadingBlock /> : null}
      {dailyAccount.error || events.error ? <ErrorState message="Could not load selected day." /> : null}

      {dailyAccount.data ? (
        <div className="grid">
          <SummaryCard title="Status" value={<TableStatusBadge status={dailyAccount.data.status} />} />
          <SummaryCard title="Target" value={formatMinutes(dailyAccount.data.target_minutes)} />
          <SummaryCard title="Actual" value={formatMinutes(dailyAccount.data.actual_minutes)} />
          <SummaryCard title="Balance" value={formatMinutes(dailyAccount.data.balance_minutes)} />
        </div>
      ) : null}

      <DataSection title="Zeitereignisliste">
        {showManualForm ? (
          <div className="inline-form">
            <p className="meta">Validierung erfolgt pro Kalendertag. Unvollständige Tage sind erlaubt.</p>
            <div className="inline-form-row">
              <label htmlFor="manual-type">Zeittyp</label>
              <select
                id="manual-type"
                value={manualType}
                onChange={(event) => {
                  setManualType(event.target.value as 'clock_in' | 'clock_out');
                  setManualDirty(true);
                }}
              >
                <option value="clock_in">Kommen (CLOCK_IN)</option>
                <option value="clock_out">Gehen (CLOCK_OUT)</option>
              </select>
            </div>
            <div className="inline-form-row">
              <label htmlFor="manual-timestamp">Zeitpunkt</label>
              <input
                id="manual-timestamp"
                type="datetime-local"
                value={manualTimestamp}
                onChange={(event) => {
                  setManualTimestamp(event.target.value);
                  setManualDirty(true);
                }}
              />
            </div>
            <div className="inline-form-row">
              <label htmlFor="manual-comment">Kommentar</label>
              <input
                id="manual-comment"
                type="text"
                maxLength={300}
                value={manualComment}
                onChange={(event) => {
                  setManualComment(event.target.value);
                  setManualDirty(true);
                }}
              />
            </div>
            <div className="actions">
              <button type="button" className="btn primary" onClick={() => void submitManualForm()} disabled={manualMutation.isPending}>
                Eintrag speichern
              </button>
              <button type="button" className="btn outline" onClick={resetManualForm}>
                Abbrechen
              </button>
            </div>
          </div>
        ) : null}

        {editError ? <p className="inline-error">{editError}</p> : null}
        {updateMutation.error ? <p className="inline-error">{String(updateMutation.error.message)}</p> : null}
        {deleteError ? <p className="inline-error">{deleteError}</p> : null}
        {deleteMutation.error ? <p className="inline-error">{String(deleteMutation.error.message)}</p> : null}
        {manualError ? <p className="inline-error">{manualError}</p> : null}
        {manualMutation.error ? <p className="inline-error">{String(manualMutation.error.message)}</p> : null}

        {!events.data?.length ? (
          <EmptyState title="Keine Einträge für diesen Tag" description="Zeitereignisse werden hier angezeigt." />
        ) : (
          <DataGrid
            columns={columns}
            data={events.data}
            searchPlaceholder="Zeitereignisse durchsuchen…"
            initialPageSize={20}
            getRowClassName={(row) => (row.id === editingRowId || row.id === deletingRowId ? 'is-editing' : undefined)}
          />
        )}
      </DataSection>
    </>
  );
}
