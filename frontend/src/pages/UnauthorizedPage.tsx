import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';

import { PageHeader } from '../components/common';
import { useAuth } from '../auth/provider';

export function UnauthorizedPage() {
  const { login, restartAuth } = useAuth();
  const location = useLocation();
  const isAuthRecovery = useMemo(() => new URLSearchParams(location.search).get('reason') === 'auth-recovery', [location.search]);

  return (
    <section className="card" style={{ maxWidth: 560, margin: '4rem auto' }}>
      <PageHeader
        title={isAuthRecovery ? 'Authentication Recovery Required' : 'Unauthorized'}
        subtitle={
          isAuthRecovery
            ? 'Your session could not be mapped to a valid internal account. Start a clean login to recover.'
            : 'You are not authenticated for this tenant context.'
        }
      />
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <button className="btn primary" onClick={restartAuth}>
          {isAuthRecovery ? 'Restart Login' : 'Reset Session & Login'}
        </button>
        <button className="btn outline" onClick={login}>
          Try Login
        </button>
      </div>
    </section>
  );
}
