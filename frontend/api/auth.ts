/**
 * Keycloak integration seam.
 *
 * Later this module will:
 * - initialize Keycloak JS adapter
 * - expose current token and tenant claims
 * - refresh tokens and attach bearer headers
 */
export type AuthContext = {
  subject: string;
  tenantId: number;
  roles: string[];
};
