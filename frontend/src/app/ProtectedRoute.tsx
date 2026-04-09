import { useEffect, useRef, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { LoadingBlock } from '../components/common';
import { useAuth } from '../auth/provider';

const LOGIN_TIMEOUT_MS = 8000;

export function ProtectedRoute() {
  const { isLoading, isAuthenticated, unauthorized, authRecoveryRequired, login } = useAuth();
  const loginRequestedRef = useRef(false);
  const [loginTimedOut, setLoginTimedOut] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !unauthorized && !authRecoveryRequired && !loginRequestedRef.current) {
      loginRequestedRef.current = true;
      console.info('[auth] protected-route: trigger login redirect');
      login();

      const timeoutId = window.setTimeout(() => {
        if (!isAuthenticated) {
          console.error('[auth] protected-route: login timeout reached without authenticated session');
          setLoginTimedOut(true);
        }
      }, LOGIN_TIMEOUT_MS);

      return () => window.clearTimeout(timeoutId);
    }

    if (isAuthenticated) {
      loginRequestedRef.current = false;
      setLoginTimedOut(false);
    }

    return undefined;
  }, [isLoading, isAuthenticated, unauthorized, authRecoveryRequired, login]);

  if (isLoading) {
    return <LoadingBlock />;
  }

  if (authRecoveryRequired || loginTimedOut) {
    return <Navigate to="/unauthorized?reason=auth-recovery" replace />;
  }

  if (unauthorized) {
    return <Navigate to="/unauthorized" replace />;
  }

  if (!isAuthenticated) {
    return <LoadingBlock />;
  }

  return <Outlet />;
}
