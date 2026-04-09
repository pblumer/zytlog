import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import Keycloak from 'keycloak-js';
import { useQuery } from '@tanstack/react-query';

import { apiGet, ApiError, setAccessTokenProvider } from '../api/client';
import { APP_CONFIG } from '../config/runtime';
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

const KEYCLOAK_URL = APP_CONFIG.keycloakUrl;
const KEYCLOAK_REALM = APP_CONFIG.keycloakRealm;
const KEYCLOAK_CLIENT_ID = APP_CONFIG.keycloakClientId;

const keycloakEnabled = Boolean(KEYCLOAK_URL && KEYCLOAK_REALM && KEYCLOAK_CLIENT_ID);
const TOKEN_REFRESH_INTERVAL_MS = 30_000;
const TOKEN_MIN_VALIDITY_SECONDS = 60;
const KEYCLOAK_INIT_TIMEOUT_MS = 10_000;
const AUTH_DEBUG_FLAG = 'zytlog_auth_debug';
const authDebugEnabled = () => window.localStorage.getItem(AUTH_DEBUG_FLAG) === '1';
const allowWeakCryptoFallback = () => import.meta.env.DEV;
const authLog = (...args: unknown[]) => {
  if (authDebugEnabled()) {
    console.info('[auth]', ...args);
  }
};

const createWeakRandomValues = <T extends ArrayBufferView | null>(typedArray: T): T => {
  if (!typedArray) {
    throw new TypeError('Expected typed array');
  }

  const view = new Uint8Array(typedArray.buffer, typedArray.byteOffset, typedArray.byteLength);
  for (let i = 0; i < view.length; i += 1) {
    view[i] = Math.floor(Math.random() * 256);
  }
  return typedArray;
};

const createWeakRandomUUID = (): `${string}-${string}-${string}-${string}-${string}` => {
  const bytes = createWeakRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
};

const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
] as const;

const rotr = (x: number, n: number) => (x >>> n) | (x << (32 - n));

const sha256Bytes = (data: Uint8Array): Uint8Array => {
  const h = new Uint32Array([
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
  ]);

  const bitLen = data.length * 8;
  const withOne = data.length + 1;
  const paddedLen = Math.ceil((withOne + 8) / 64) * 64;
  const padded = new Uint8Array(paddedLen);
  padded.set(data);
  padded[data.length] = 0x80;

  const view = new DataView(padded.buffer);
  view.setUint32(paddedLen - 8, Math.floor(bitLen / 2 ** 32), false);
  view.setUint32(paddedLen - 4, bitLen >>> 0, false);

  const w = new Uint32Array(64);

  for (let offset = 0; offset < paddedLen; offset += 64) {
    for (let i = 0; i < 16; i += 1) {
      w[i] = view.getUint32(offset + i * 4, false);
    }
    for (let i = 16; i < 64; i += 1) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = (((w[i - 16] + s0) >>> 0) + ((w[i - 7] + s1) >>> 0)) >>> 0;
    }

    let a = h[0];
    let b = h[1];
    let c = h[2];
    let d = h[3];
    let e = h[4];
    let f = h[5];
    let g = h[6];
    let j = h[7];

    for (let i = 0; i < 64; i += 1) {
      const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (((((j + S1) >>> 0) + ch) >>> 0) + ((SHA256_K[i] + w[i]) >>> 0)) >>> 0;
      const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (S0 + maj) >>> 0;

      j = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    h[0] = (h[0] + a) >>> 0;
    h[1] = (h[1] + b) >>> 0;
    h[2] = (h[2] + c) >>> 0;
    h[3] = (h[3] + d) >>> 0;
    h[4] = (h[4] + e) >>> 0;
    h[5] = (h[5] + f) >>> 0;
    h[6] = (h[6] + g) >>> 0;
    h[7] = (h[7] + j) >>> 0;
  }

  const out = new Uint8Array(32);
  const outView = new DataView(out.buffer);
  for (let i = 0; i < h.length; i += 1) {
    outView.setUint32(i * 4, h[i], false);
  }
  return out;
};

const createWeakSubtleCrypto = (): SubtleCrypto =>
  ({
    digest: async (algorithm: AlgorithmIdentifier, data: BufferSource) => {
      const name = typeof algorithm === 'string' ? algorithm : algorithm.name;
      if (name.toUpperCase() !== 'SHA-256') {
        throw new Error(`Unsupported digest algorithm: ${name}`);
      }
      const bytes = data instanceof ArrayBuffer ? new Uint8Array(data) : new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
      const digest = sha256Bytes(bytes);
      return digest.buffer;
    },
  }) as SubtleCrypto;

const ensureCryptoForKeycloak = () => {
  if (typeof window === 'undefined') {
    return;
  }

  const globalRef = globalThis as typeof globalThis & { crypto?: Crypto };
  const existingCrypto = globalRef.crypto ?? (window as Window & { crypto?: Crypto }).crypto;

  const hasGetRandomValues = Boolean(existingCrypto && typeof existingCrypto.getRandomValues === 'function');
  const hasRandomUUID = Boolean(existingCrypto && typeof (existingCrypto as Crypto & { randomUUID?: () => string }).randomUUID === 'function');
  const hasSubtleDigest = Boolean(existingCrypto?.subtle && typeof existingCrypto.subtle.digest === 'function');

  authLog('crypto capabilities before patch', {
    hasCryptoObject: Boolean(existingCrypto),
    hasGetRandomValues,
    hasRandomUUID,
    hasSubtleDigest,
    isSecureContext: window.isSecureContext,
  });

  if (hasGetRandomValues && hasRandomUUID && hasSubtleDigest) {
    return;
  }

  if (!allowWeakCryptoFallback()) {
    console.error('[auth] Web Crypto API incomplete/unavailable and weak fallback is disabled for this environment');
    return;
  }

  console.warn('[auth] Web Crypto API incomplete/unavailable, installing local-dev fallback');

  const patchedCrypto = (existingCrypto ?? {}) as Crypto & { randomUUID?: () => string };

  if (typeof patchedCrypto.getRandomValues !== 'function') {
    patchedCrypto.getRandomValues = createWeakRandomValues;
  }

  if (typeof patchedCrypto.randomUUID !== 'function') {
    patchedCrypto.randomUUID = createWeakRandomUUID;
  }

  if (!patchedCrypto.subtle || typeof patchedCrypto.subtle.digest !== 'function') {
    Object.defineProperty(patchedCrypto, 'subtle', {
      value: createWeakSubtleCrypto(),
      configurable: true,
    });
  }

  try {
    Object.defineProperty(globalRef, 'crypto', {
      value: patchedCrypto,
      configurable: true,
    });
  } catch {
    globalRef.crypto = patchedCrypto;
  }

  try {
    Object.defineProperty(window, 'crypto', {
      value: patchedCrypto,
      configurable: true,
    });
  } catch {
    (window as Window & { crypto?: Crypto }).crypto = patchedCrypto;
  }

  authLog('crypto capabilities after patch', {
    hasCryptoObject: Boolean(globalRef.crypto),
    hasGetRandomValues: Boolean(globalRef.crypto && typeof globalRef.crypto.getRandomValues === 'function'),
    hasRandomUUID: Boolean(globalRef.crypto && typeof (globalRef.crypto as Crypto & { randomUUID?: () => string }).randomUUID === 'function'),
    hasSubtleDigest: Boolean(globalRef.crypto?.subtle && typeof globalRef.crypto.subtle.digest === 'function'),
  });
};

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

    ensureCryptoForKeycloak();

    const keycloak = new Keycloak({
      url: KEYCLOAK_URL!,
      realm: KEYCLOAK_REALM!,
      clientId: KEYCLOAK_CLIENT_ID!,
    });

    keycloakRef.current = keycloak;

    let cancelled = false;
    let initTimedOut = false;

    const usePkce = true; // Keycloak client requires PKCE in this environment.

    const initTimeoutId = window.setTimeout(() => {
      if (cancelled || authBootstrapped) return;
      initTimedOut = true;
      console.error('[auth] keycloak init timeout', {
        keycloakUrl: KEYCLOAK_URL,
        realm: KEYCLOAK_REALM,
        clientId: KEYCLOAK_CLIENT_ID,
        location: window.location.href,
      });
      setAccessToken(null);
      setAuthBootstrapped(true);
    }, KEYCLOAK_INIT_TIMEOUT_MS);

    authLog('keycloak init start', {
      keycloakUrl: KEYCLOAK_URL,
      realm: KEYCLOAK_REALM,
      clientId: KEYCLOAK_CLIENT_ID,
      usePkce,
      isSecureContext: window.isSecureContext,
      hostname: window.location.hostname,
    });

    keycloak
      .init({
        onLoad: 'login-required',
        pkceMethod: usePkce ? ('S256' as const) : false,
        responseMode: 'query',
        checkLoginIframe: false,
      })
      .then((authenticated: boolean) => {
        window.clearTimeout(initTimeoutId);
        if (cancelled || initTimedOut) return;

        authLog('keycloak init resolved', { authenticated, hasToken: Boolean(keycloak.token) });

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
      .catch((error: unknown) => {
        window.clearTimeout(initTimeoutId);
        if (cancelled || initTimedOut) return;
        console.error('[auth] keycloak init failed', error);
        setAccessToken(null);
        setAuthBootstrapped(true);
      });

    return () => {
      cancelled = true;
      window.clearTimeout(initTimeoutId);
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
    authLog('login called', { hasKeycloak: Boolean(keycloakRef.current) });
    setAccessToken(null);
    if (keycloakRef.current) {
      void keycloakRef.current.login({ prompt: 'login' }).catch((error: unknown) => {
        console.error('[auth] login failed', error);
      });
      return;
    }
    window.location.assign('/');
  };

  const unauthorized = !isRefreshingToken && meQuery.error instanceof ApiError && meQuery.error.status === 401;
  const authRecoveryRequired =
    !isRefreshingToken &&
    meQuery.error instanceof ApiError &&
    (meQuery.error.status >= 500 || meQuery.error.status === 403);

  useEffect(() => {
    if (!authDebugEnabled()) return;

    authLog('state', {
      authBootstrapped,
      isRefreshingToken,
      hasToken: Boolean(effectiveToken),
      meLoading: meQuery.isLoading,
      meError: meQuery.error
        ? {
            name: meQuery.error.name,
            message: meQuery.error.message,
            status: meQuery.error instanceof ApiError ? meQuery.error.status : null,
          }
        : null,
      unauthorized,
      authRecoveryRequired,
      isAuthenticated: Boolean(meQuery.data),
    });
  }, [authBootstrapped, isRefreshingToken, effectiveToken, meQuery.isLoading, meQuery.error, meQuery.data, unauthorized, authRecoveryRequired]);

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
