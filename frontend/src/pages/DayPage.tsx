import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { DayTimeline } from '../components/DayTimeline';
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
import { formatDate, formatMinutes, isoDate } from '../utils/date';
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

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
  const dayStatus = dailyAccount.data?.status;
  const isInvalidDay = dayStatus === 'invalid';

  const statusContent =
    dayStatus === 'complete'
      ? { tone: 'success', text: 'OK – gültige Zeiterfassung' }
      : dayStatus === 'incomplete'
        ? { tone: 'warning', text: 'Unvollständig – es fehlt ein Gegenstempel' }
        : dayStatus === 'invalid'
          ? { tone: 'danger', text: 'Ungültige Sequenz' }
          : { tone: 'neutral', text: 'Keine Daten' };

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
                aria-label={`Zeitpunkt für Eintrag um ${formatTime(row.timestamp)} bearbeiten`}
                onChange={(event) => setDraft((prev) => (prev ? { ...prev, timestamp: event.target.value } : prev))}
              />
            );
          }
          return <span className="time-value">{formatTime(row.timestamp)}</span>;
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
                aria-label={`Kommentar für Eintrag um ${formatTime(row.timestamp)} bearbeiten`}
                onChange={(event) => setDraft((prev) => (prev ? { ...prev, comment: event.target.value } : prev))}
              />
            );
          }
          if (!row.comment) return <span className="comment-placeholder">—</span>;
          return (
            <span className="comment-text" title={row.comment}>
              {row.comment}
            </span>
          );
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
              <button
                type="button"
                className="btn secondary"
                aria-label={`Eintrag von ${formatTime(row.timestamp)} bearbeiten`}
                onClick={() => startEdit(row)}
                disabled={deletingRowId === row.id}
              >
                Bearbeiten
              </button>
              <button
                type="button"
                className="btn danger"
                aria-label={`Eintrag von ${formatTime(row.timestamp)} löschen`}
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
              aria-label="Datum auswählen"
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
              aria-expanded={showManualForm}
              aria-controls="manual-entry-form"
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
      {dailyAccount.error || events.error ? <ErrorState message="Ausgewählter Tag konnte nicht geladen werden." /> : null}

      {dailyAccount.data ? (
        <section className="grid" aria-label="Tageszusammenfassung">
          <SummaryCard
            title="Status"
            value={<span className={`status ${statusContent.tone}`}>{statusContent.text}</span>}
            hint={
              isInvalidDay ? (
                <span>
                  Die Reihenfolge der Zeitstempel ist nicht korrekt.
                  <br />
                  Du kannst Einträge bearbeiten oder löschen, um den Tag zu korrigieren.
                </span>
              ) : undefined
            }
          />
          <SummaryCard title="Soll" value={<span className="time-value">{formatMinutes(dailyAccount.data.target_minutes)}</span>} />
          {dailyAccount.data.is_holiday ? (
            <SummaryCard title="Feiertag" value={dailyAccount.data.holiday_name ?? 'Ja'} hint="Sollzeit am Feiertag ist immer 0." />
          ) : null}
          <SummaryCard title="Ist" value={<span className="time-value">{formatMinutes(dailyAccount.data.actual_minutes)}</span>} />
          <SummaryCard
            title="Saldo"
            value={
              <span
                className={`time-value ${dailyAccount.data.balance_minutes > 0 ? 'balance-positive' : dailyAccount.data.balance_minutes < 0 ? 'balance-negative' : 'balance-neutral'}`}
              >
                {formatMinutes(dailyAccount.data.balance_minutes)}
              </span>
            }
          />
        </section>
      ) : null}


      <DataSection title="Zeitverlauf">
        <p className="meta">Chronologische Darstellung deiner Zeitereignisse.</p>
        <DayTimeline events={events.data ?? []} status={dailyAccount.data?.status} />
      </DataSection>

      <DataSection title={`Zeitereignisliste${isInvalidDay ? ' ⚠️' : ''}`}>
        <p className="meta">Datum: {formatDate(date)}</p>
        {showManualForm ? (
          <form
            id="manual-entry-form"
            className="inline-form"
            aria-label="Zeitstempel manuell nacherfassen"
            onSubmit={(event) => {
              event.preventDefault();
              void submitManualForm();
            }}
          >
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
                <option value="clock_in">Kommen</option>
                <option value="clock_out">Gehen</option>
              </select>
            </div>
            <div className="inline-form-row">
              <label htmlFor="manual-timestamp">Zeitpunkt</label>
              <input
                id="manual-timestamp"
                type="datetime-local"
                value={manualTimestamp}
                required
                aria-invalid={Boolean(manualError)}
                aria-describedby={manualError ? 'manual-form-error' : undefined}
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
                aria-describedby="manual-comment-hint"
                onChange={(event) => {
                  setManualComment(event.target.value);
                  setManualDirty(true);
                }}
              />
              <p id="manual-comment-hint" className="meta">
                Optional, maximal 300 Zeichen.
              </p>
            </div>
            <div className="actions">
              <button type="submit" className="btn primary" disabled={manualMutation.isPending}>
                Eintrag speichern
              </button>
              <button type="button" className="btn outline" onClick={resetManualForm}>
                Abbrechen
              </button>
            </div>
          </form>
        ) : null}

        {editError ? <p className="inline-error" role="alert">{editError}</p> : null}
        {updateMutation.error ? <p className="inline-error" role="alert">{String(updateMutation.error.message)}</p> : null}
        {deleteError ? <p className="inline-error" role="alert">{deleteError}</p> : null}
        {deleteMutation.error ? <p className="inline-error" role="alert">{String(deleteMutation.error.message)}</p> : null}
        {manualError ? <p id="manual-form-error" className="inline-error" role="alert">{manualError}</p> : null}
        {manualMutation.error ? <p className="inline-error" role="alert">{String(manualMutation.error.message)}</p> : null}

        {!events.data?.length ? (
          <EmptyState title="Keine Zeitstempel vorhanden" description="Erfasse deinen ersten Zeitstempel über 'Kommen'" />
        ) : (
          <div className={isInvalidDay ? 'day-events day-events-invalid' : 'day-events'}>
            <DataGrid
              columns={columns}
              data={events.data}
              searchPlaceholder="Zeitereignisse durchsuchen…"
              initialPageSize={20}
              getRowClassName={(row) => (row.id === editingRowId || row.id === deletingRowId ? 'is-editing' : undefined)}
            />
          </div>
        )}
      </DataSection>
    </>
  );
}
