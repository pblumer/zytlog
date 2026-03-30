import type { PropsWithChildren, ReactNode } from 'react';

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <h1>{title}</h1>
      {subtitle ? <p>{subtitle}</p> : null}
      {actions ? <div className="actions" style={{ marginTop: '0.75rem' }}>{actions}</div> : null}
    </div>
  );
}

export function SummaryCard({ title, value, hint }: { title: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <article className="card">
      <h3>{title}</h3>
      <div style={{ fontSize: '1.2rem', fontWeight: 600 }}>{value}</div>
      {hint ? <div className="meta">{hint}</div> : null}
    </article>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status.includes('complete') || status.includes('clocked_in')
      ? 'success'
      : status.includes('incomplete')
        ? 'warning'
        : status.includes('invalid')
          ? 'danger'
          : 'neutral';

  return <span className={`status ${tone}`}>{status.replace('_', ' ')}</span>;
}

export function LoadingBlock() {
  return <div className="card">Loading…</div>;
}

export function ErrorState({ message }: { message?: string }) {
  return <div className="card">Error: {message ?? 'Something went wrong.'}</div>;
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="card">
      <strong>{title}</strong>
      {description ? <p className="meta">{description}</p> : null}
    </div>
  );
}

export function DataSection({ title, children }: PropsWithChildren<{ title: string }>) {
  return (
    <section className="card">
      <h3>{title}</h3>
      {children}
    </section>
  );
}
