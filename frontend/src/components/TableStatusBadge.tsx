const STATUS_LABELS: Record<string, string> = {
  clock_in: 'Kommen',
  clock_out: 'Gehen',
  clocked_in: 'Eingestempelt',
  clocked_out: 'Ausgestempelt',
  complete: 'OK',
  incomplete: 'Unvollständig',
  invalid: 'Ungültig',
  active: 'Aktiv',
  empty: 'Keine Daten',
  no_data: 'Keine Daten',
};

export function TableStatusBadge({ status }: { status: string }) {
  const tone =
    status === 'complete' || status === 'clocked_in' || status === 'active'
      ? 'success'
      : status === 'clock_in'
        ? 'info'
        : status === 'clock_out' || status === 'clocked_out'
          ? 'neutral'
          : status === 'incomplete'
            ? 'warning'
            : status === 'invalid'
              ? 'danger'
              : 'neutral';

  return <span className={`status ${tone}`}>{STATUS_LABELS[status] ?? status.replace('_', ' ')}</span>;
}
