import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../auth/provider';
import { LoadingBlock } from '../components/common';

export function ProtectedRoute() {
  const { isLoading, isAuthenticated, unauthorized, authRecoveryRequired } = useAuth();

  if (isLoading) {
    return <LoadingBlock />;
  }

  if (authRecoveryRequired) {
    return <Navigate to="/unauthorized?reason=auth-recovery" replace />;
  }

  if (unauthorized || !isAuthenticated) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
