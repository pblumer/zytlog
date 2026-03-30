import { useMemo, useState } from 'react';

import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader, SummaryCard } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { InlineEditActions } from '../components/InlineEditActions';
import { ReportExportActions } from '../components/ReportExportActions';
import { TableStatusBadge } from '../components/TableStatusBadge';
import { useReportExport } from '../hooks/useReportExport';
import { useDailyAccount, useTimeStamps, useUpdateTimeStampMutation } from '../hooks/useZytlogApi';
import type { TimeStampEvent } from '../types/api';
import { formatDateTime, formatMinutes, isoDate } from '../utils/date';

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
  const [date, setDate] = useState(isoDate(new Date()));
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [draft, setDraft] = useState<EditDraft | null>(null);
  const [editError, setEditError] = useState<string | null>(null);

  const dailyAccount = useDailyAccount(date);
  const events = useTimeStamps(date, date);
  const updateMutation = useUpdateTimeStampMutation();
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

  const columns = useMemo<DataGridColumn<TimeStampEvent>[]>(
    () => [
      {
        id: 'type',
        header: 'Type',
        cell: (row) => <TableStatusBadge status={row.type} />,
        sortValue: (row) => row.type,
        searchableText: (row) => row.type,
        sortable: true,
      },
      {
        id: 'timestamp',
        header: 'Timestamp',
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
        header: 'Comment',
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
        header: 'Corrected',
        cell: (row) => (new Date(row.updated_at).getTime() > new Date(row.created_at).getTime() ? 'Yes' : 'No'),
        sortValue: (row) => row.updated_at,
        searchableText: (row) => row.updated_at,
        sortable: true,
      },
      {
        id: 'actions',
        header: 'Actions',
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
            <button type="button" className="btn outline" onClick={() => startEdit(row)}>
              Edit
            </button>
          );
        },
      },
    ],
    [draft, editingRowId, updateMutation.isPending],
  );

  return (
    <>
      <PageHeader
        title="Day"
        subtitle="Inspect one day in detail"
        actions={
          <>
            <input
              type="date"
              value={date}
              onChange={(event) => {
                setDate(event.target.value);
                exporter.clearError();
              }}
            />
            <ReportExportActions disabled={exporter.isExporting} onExport={(format) => void exporter.exportDay(date, format)} />
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

      <DataSection title="Event List">
        {editError ? <p className="inline-error">{editError}</p> : null}
        {updateMutation.error ? <p className="inline-error">{String(updateMutation.error.message)}</p> : null}

        {!events.data?.length ? (
          <EmptyState title="No events for this day" description="Time stamp events will appear here." />
        ) : (
          <DataGrid
            columns={columns}
            data={events.data}
            searchPlaceholder="Search events…"
            initialPageSize={20}
            getRowClassName={(row) => (row.id === editingRowId ? 'is-editing' : undefined)}
          />
        )}
      </DataSection>
    </>
  );
}
