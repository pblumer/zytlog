import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="card centered-card">
      <h1>Seite nicht gefunden</h1>
      <p>Die angeforderte Seite existiert nicht oder wurde verschoben.</p>
      <Link to="/dashboard" className="btn primary">Zum Dashboard</Link>
    </section>
  );
}