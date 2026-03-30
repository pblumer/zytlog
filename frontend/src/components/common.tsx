import { TableStatusBadge } from './TableStatusBadge';
import type { PropsWithChildren, ReactNode } from 'react';

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <header className="page-header">
      <h1>{title}</h1>
      {subtitle ? <p>{subtitle}</p> : null}
      {actions ? (
        <div className="actions page-header-actions" style={{ marginTop: '0.75rem' }} aria-label={`${title} Aktionen`}>
          {actions}
        </div>
      ) : null}
    </header>
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
  return <TableStatusBadge status={status} />;
}

export function LoadingBlock() {
  return <div className="card" role="status" aria-live="polite">Loading…</div>;
}

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="card inline-error" role="alert">
      Error: {message ?? 'Something went wrong.'}
    </div>
  );
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
