import { useMemo } from 'react';

import { useClockMutation } from '../hooks/useZytlogApi';
import type { ClockStatus } from '../types/api';
import { formatDateTime } from '../utils/date';
import { ErrorState, StatusBadge } from './common';

type Props = {
  status: ClockStatus;
  lastEventTimestamp?: string | null;
  title?: string;
};

export function QuickStampCard({ status, lastEventTimestamp, title = 'Schnellerfassung' }: Props) {
  const clockIn = useClockMutation('in');
  const clockOut = useClockMutation('out');

  const nextAction = status === 'clocked_in' ? 'clock_out' : 'clock_in';
  const actionLabel = nextAction === 'clock_in' ? 'Kommen' : 'Gehen';
  const isPending = clockIn.isPending || clockOut.isPending;

  const errorMessage = useMemo(() => {
    if (nextAction === 'clock_in' && clockIn.error) return clockIn.error.message;
    if (nextAction === 'clock_out' && clockOut.error) return clockOut.error.message;
    return null;
  }, [clockIn.error, clockOut.error, nextAction]);

  return (
    <section className="card" style={{ marginTop: '1rem' }}>
      <h3>{title}</h3>
      <p className="meta">
        Aktueller Status: <StatusBadge status={status} />
      </p>
      <button
        type="button"
        className="btn primary quick-stamp-btn"
        disabled={isPending}
        onClick={() => {
          if (nextAction === 'clock_in') {
            clockIn.mutate();
            return;
          }
          clockOut.mutate();
        }}
      >
        {isPending ? 'Wird gespeichert…' : actionLabel}
      </button>
      <p className="meta">{lastEventTimestamp ? `Letztes Ereignis: ${formatDateTime(lastEventTimestamp)}` : 'Noch keine Buchung vorhanden.'}</p>
      {errorMessage ? <ErrorState message={errorMessage} /> : null}
    </section>
  );
}
