import { useEffect, useMemo, useState } from 'react';

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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const nextAction = status === 'clocked_in' ? 'clock_out' : 'clock_in';
  const actionLabel = nextAction === 'clock_in' ? 'Kommen (Jetzt)' : 'Gehen (Jetzt)';
  const actionLabelWithTime = `${nextAction === 'clock_in' ? 'Kommen' : 'Gehen'} – ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  const isPending = clockIn.isPending || clockOut.isPending;

  const errorMessage = useMemo(() => {
    if (nextAction === 'clock_in' && clockIn.error) return clockIn.error.message;
    if (nextAction === 'clock_out' && clockOut.error) return clockOut.error.message;
    return null;
  }, [clockIn.error, clockOut.error, nextAction]);

  useEffect(() => {
    if (!successMessage) return;
    const timer = window.setTimeout(() => setSuccessMessage(null), 2200);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  return (
    <section className="card section-gap">
      <h3>{title}</h3>
      <p className="meta">
        Aktueller Status: <StatusBadge status={status} />
      </p>
      <button
        type="button"
        className="btn primary quick-stamp-btn"
        disabled={isPending}
        aria-label={actionLabel}
        onClick={async () => {
          try {
            if (nextAction === 'clock_in') {
              await clockIn.mutateAsync();
            } else {
              await clockOut.mutateAsync();
            }
            setSuccessMessage('Zeitstempel erfasst');
          } catch {
            setSuccessMessage(null);
          }
        }}
      >
        {isPending ? <span className="btn-spinner" aria-label="Speichern" /> : actionLabel}
      </button>
      <p className="meta quick-stamp-preview">{actionLabelWithTime}</p>
      <p className="meta">{lastEventTimestamp ? `Letztes Ereignis: ${formatDateTime(lastEventTimestamp)}` : 'Noch keine Buchung vorhanden.'}</p>
      {successMessage ? (
        <p className="quick-stamp-success" role="status" aria-live="polite">
          {successMessage}
        </p>
      ) : null}
      {errorMessage ? <ErrorState message={errorMessage} /> : null}
    </section>
  );
}
