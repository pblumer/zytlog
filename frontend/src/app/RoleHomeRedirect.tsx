import { Navigate } from 'react-router-dom';

import { useAuth } from '../auth/provider';
import { getDefaultRouteForRole } from '../auth/roleRouting';
import { LoadingBlock } from '../components/common';

export function RoleHomeRedirect() {
  const { isLoading, user } = useAuth();

  if (isLoading || !user) {
    return <LoadingBlock />;
  }

  return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
}
