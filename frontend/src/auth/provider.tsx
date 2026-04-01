import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import Keycloak from 'keycloak-js';
import { useQuery } from '@tanstack/react-query';

import { apiGet, ApiError, setAccessTokenProvider } from '../api/client';
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
  authRecoveryRequired: boolean;
  restartAuth: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

const STORAGE_KEY = 'zytlog_access_token';
const getStoredToken = () => localStorage.getItem(STORAGE_KEY);

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL;
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM;
const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID;

const keycloakEnabled = Boolean(KEYCLOAK_URL && KEYCLOAK_REALM && KEYCLOAK_CLIENT_ID);
const TOKEN_REFRESH_INTERVAL_MS = 25_000;
const TOKEN_MIN_VALIDITY_SECONDS = 60;

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => getStoredToken() ?? import.meta.env.VITE_DEV_BEARER_TOKEN ?? null);
  const [authBootstrapped, setAuthBootstrapped] = useState(!keycloakEnabled);
  const [isRefreshingToken, setIsRefreshingToken] = useState(false);
  const keycloakRef = useRef<Keycloak | null>(null);
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null);
  const tokenRef = useRef(token);

  const setAccessToken = useCallback((value: string | null) => {
    if (value) localStorage.setItem(STORAGE_KEY, value);
    else localStorage.removeItem(STORAGE_KEY);
    setToken(value);
  }, []);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const refreshAccessToken = useCallback(
    async (minValidity: number) => {
      const keycloak = keycloakRef.current;
      if (!keycloakEnabled || !keycloak) {
        return tokenRef.current ?? getStoredToken();
      }

      if (refreshPromiseRef.current) {
        return refreshPromiseRef.current;
      }

      const currentToken = keycloak.token ?? tokenRef.current ?? getStoredToken();
      const exp = keycloak.tokenParsed?.exp;
      const now = Math.floor(Date.now() / 1000);
      const needsRefresh = !exp || exp - now <= minValidity;

      if (!needsRefresh) {
        if (keycloak.token && keycloak.token !== tokenRef.current) {
          setAccessToken(keycloak.token);
        }
        return currentToken;
      }

      setIsRefreshingToken(true);
      const refreshPromise = keycloak
        .updateToken(minValidity)
        .then(() => {
          const nextToken = keycloak.token ?? null;
          setAccessToken(nextToken);
          return nextToken;
        })
        .catch(() => {
          if (!keycloak.authenticated) {
            setAccessToken(null);
            return null;
          }
          return currentToken ?? null;
        })
        .finally(() => {
          refreshPromiseRef.current = null;
          setIsRefreshingToken(false);
        });

      refreshPromiseRef.current = refreshPromise;
      return refreshPromise;
    },
    [setAccessToken],
  );

  const getValidAccessToken = useCallback(async () => {
    if (!keycloakEnabled) {
      return tokenRef.current ?? getStoredToken();
    }
    return refreshAccessToken(TOKEN_MIN_VALIDITY_SECONDS);
  }, [refreshAccessToken]);

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
      .then((authenticated: boolean) => {
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
          void refreshAccessToken(TOKEN_MIN_VALIDITY_SECONDS);
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
  }, [refreshAccessToken, setAccessToken]);

  useEffect(() => {
    if (!keycloakEnabled || !authBootstrapped || !keycloakRef.current?.authenticated) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void refreshAccessToken(TOKEN_MIN_VALIDITY_SECONDS);
    }, TOKEN_REFRESH_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [authBootstrapped, refreshAccessToken]);

  useEffect(() => {
    setAccessTokenProvider(getValidAccessToken);
    return () => setAccessTokenProvider(null);
  }, [getValidAccessToken]);

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

  const unauthorized = !isRefreshingToken && meQuery.error instanceof ApiError && meQuery.error.status === 401;
  const authRecoveryRequired =
    !isRefreshingToken &&
    meQuery.error instanceof ApiError &&
    (meQuery.error.status >= 500 || meQuery.error.status === 403);

  const restartAuth = () => {
    setAccessToken(null);
    if (keycloakRef.current) {
      void keycloakRef.current.logout({ redirectUri: `${window.location.origin}/` });
      return;
    }
    window.location.assign('/');
  };

  const value = useMemo<AuthState>(
    () => ({
      user: meQuery.data ?? null,
      token: effectiveToken,
      isLoading: !authBootstrapped || meQuery.isLoading || isRefreshingToken,
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
      authRecoveryRequired,
      restartAuth,
    }),
    [authBootstrapped, meQuery.data, meQuery.isLoading, effectiveToken, isRefreshingToken, unauthorized, authRecoveryRequired, setAccessToken],
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
