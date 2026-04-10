import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="card" style={{ maxWidth: 560, margin: '3rem auto' }} role="alert">
      <h1 style={{ fontSize: '1.25rem', margin: 0 }}>Seite nicht gefunden</h1>
      <p className="meta" style={{ marginTop: '0.5rem' }}>
        Die angeforderte Seite existiert nicht oder wurde verschoben.
      </p>
      <div className="actions" style={{ marginTop: '1rem' }}>
        <Link to="/dashboard" className="btn">Zum Dashboard</Link>
      </div>
    </section>
  );
}
