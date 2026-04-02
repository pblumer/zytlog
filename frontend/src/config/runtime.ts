type RuntimeConfig = {
  API_BASE_URL?: string;
  KEYCLOAK_URL?: string;
  KEYCLOAK_REALM?: string;
  KEYCLOAK_CLIENT_ID?: string;
};

declare global {
  interface Window {
    __APP_CONFIG__?: RuntimeConfig;
  }
}

const runtimeConfig = window.__APP_CONFIG__ ?? {};

const readValue = (runtimeValue: string | undefined, viteValue: string | undefined) => {
  const trimmedRuntime = runtimeValue?.trim();
  if (trimmedRuntime) return trimmedRuntime;

  const trimmedVite = viteValue?.trim();
  if (trimmedVite) return trimmedVite;

  return undefined;
};

export const APP_CONFIG = {
  apiBaseUrl: readValue(runtimeConfig.API_BASE_URL, import.meta.env.VITE_API_BASE_URL) ?? 'http://localhost:8000/api/v1',
  keycloakUrl: readValue(runtimeConfig.KEYCLOAK_URL, import.meta.env.VITE_KEYCLOAK_URL),
  keycloakRealm: readValue(runtimeConfig.KEYCLOAK_REALM, import.meta.env.VITE_KEYCLOAK_REALM),
  keycloakClientId: readValue(runtimeConfig.KEYCLOAK_CLIENT_ID, import.meta.env.VITE_KEYCLOAK_CLIENT_ID),
} as const;
