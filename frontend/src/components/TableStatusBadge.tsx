export function TableStatusBadge({ status }: { status: string }) {
  const tone =
    status === 'complete' || status === 'clocked_in' || status === 'active'
      ? 'success'
      : status === 'incomplete'
        ? 'warning'
        : status === 'invalid'
          ? 'danger'
          : 'neutral';

  return <span className={`status ${tone}`}>{status.replace('_', ' ')}</span>;
}
