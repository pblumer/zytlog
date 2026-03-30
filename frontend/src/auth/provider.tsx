import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import Keycloak from 'keycloak-js';
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
const getStoredToken = () => localStorage.getItem(STORAGE_KEY);

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL;
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM;
const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;

const keycloakEnabled = Boolean(KEYCLOAK_URL && KEYCLOAK_REALM && KEYCLOAK_CLIENT_ID);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => getStoredToken() ?? import.meta.env.VITE_DEV_BEARER_TOKEN ?? null);
  const [authBootstrapped, setAuthBootstrapped] = useState(!keycloakEnabled);
  const keycloakRef = useRef<Keycloak | null>(null);

  const setAccessToken = useCallback((value: string | null) => {
    if (value) localStorage.setItem(STORAGE_KEY, value);
    else localStorage.removeItem(STORAGE_KEY);
    setToken(value);
  }, []);

  useEffect(() => {
    if (!keycloakEnabled) return;

    const keycloak = new Keycloak({
      url: KEYCLOAK_URL,
      realm: KEYCLOAK_REALM,
      clientId: KEYCLOAK_CLIENT_ID,
    });

    keycloakRef.current = keycloak;

    let cancelled = false;

    keycloak
      .init({
        onLoad: 'login-required',
        pkceMethod: 'S256',
        responseMode: 'query',
        checkLoginIframe: false,
      })
      .then((authenticated) => {
        if (cancelled) return;

        if (!authenticated) {
          setAccessToken(null);
          setAuthBootstrapped(true);
          return;
        }

        setAccessToken(keycloak.token ?? null);

        if (window.location.search.includes('code=')) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }

        keycloak.onAuthSuccess = () => {
          setAccessToken(keycloak.token ?? null);
        };

        keycloak.onAuthRefreshSuccess = () => {
          setAccessToken(keycloak.token ?? null);
        };

        keycloak.onAuthLogout = () => {
          setAccessToken(null);
        };

        keycloak.onTokenExpired = () => {
          keycloak
            .updateToken(30)
            .then(() => {
              setAccessToken(keycloak.token ?? null);
            })
            .catch(() => {
              void keycloak.login();
            });
        };

        setAuthBootstrapped(true);
      })
      .catch(() => {
        if (cancelled) return;
        setAccessToken(null);
        setAuthBootstrapped(true);
      });

    return () => {
      cancelled = true;
    };
  }, [setAccessToken]);

  const effectiveToken = token ?? getStoredToken();

  const meQuery = useQuery({
    queryKey: ['me', effectiveToken],
    queryFn: () => apiGet<Me>('/me', effectiveToken),
    retry: false,
    enabled: authBootstrapped && Boolean(effectiveToken),
  });

  const login = () => {
    if (keycloakRef.current) {
      void keycloakRef.current.login();
      return;
    }
    window.location.assign('/');
  };

  const unauthorized = meQuery.error instanceof ApiError && meQuery.error.status === 401;

  const value = useMemo<AuthState>(
    () => ({
      user: meQuery.data ?? null,
      token: effectiveToken,
      isLoading: !authBootstrapped || meQuery.isLoading,
      isAuthenticated: Boolean(meQuery.data),
      isAdmin: meQuery.data?.role === 'admin',
      login,
      logout: () => {
        setAccessToken(null);
        if (keycloakRef.current) {
          void keycloakRef.current.logout({ redirectUri: window.location.origin });
        }
      },
      unauthorized,
    }),
    [authBootstrapped, meQuery.data, meQuery.isLoading, effectiveToken, unauthorized, setAccessToken],
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