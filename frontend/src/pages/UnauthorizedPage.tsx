import { PageHeader } from '../components/common';
import { useAuth } from '../auth/provider';

export function UnauthorizedPage() {
  const { login } = useAuth();

  return (
    <section className="card" style={{ maxWidth: 560, margin: '4rem auto' }}>
      <PageHeader title="Unauthorized" subtitle="You are not authenticated for this tenant context." />
      <button className="btn primary" onClick={login}>
        Go to Login
      </button>
    </section>
  );
}
