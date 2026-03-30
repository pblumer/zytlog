import { createContext, useContext, useMemo, useState, type PropsWithChildren } from 'react';
import { useQuery } from '@tanstack/react-query';

import { apiGet, ApiError } from '../api/client';
import type { Me } from '../types/api';

type AuthState = {
  user: Me | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: () => void;
  logout: () => void;
  unauthorized: boolean;
};

const AuthContext = createContext<AuthState | null>(null);

const STORAGE_KEY = 'zytlog_access_token';

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY) ?? import.meta.env.VITE_DEV_BEARER_TOKEN ?? null);

  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: () => apiGet<Me>('/me', token),
    retry: false,
  });

  const login = () => {
    // Keycloak integration seam: future implementation should redirect to Keycloak login.
    // For now this keeps a single place for auth initiation.
    window.location.assign('/');
  };

  // Integration seam for future Keycloak callback/token exchange flow.
  const setAccessToken = (value: string | null) => {
    if (value) localStorage.setItem(STORAGE_KEY, value);
    else localStorage.removeItem(STORAGE_KEY);
    setToken(value);
  };

  const unauthorized = meQuery.error instanceof ApiError && meQuery.error.status === 401;

  const value = useMemo<AuthState>(
    () => ({
      user: meQuery.data ?? null,
      token,
      isLoading: meQuery.isLoading,
      isAuthenticated: Boolean(meQuery.data),
      isAdmin: meQuery.data?.role === 'admin',
      login,
      logout: () => {
        setAccessToken(null);
      },
      unauthorized,
    }),
    [meQuery.data, meQuery.isLoading, token, unauthorized],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
