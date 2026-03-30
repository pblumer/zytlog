# Keycloak local setup for Zytlog

Use this guide to provision a local realm and API client that matches backend JWT validation.

## 1) Start Keycloak

```bash
docker compose up -d keycloak
```

Open `http://localhost:8080` and sign in with:
- username: `admin`
- password: `admin`

## 2) Create realm

- Create realm: `zytlog`

## 3) Create API client

Create client:
- Client ID: `zytlog-api`
- Client type: OpenID Connect
- Access type: `confidential` (or `public` for early local testing)
- Standard flow: enabled
- Direct access grants: enabled for manual token testing

For local frontend development, add redirect URI:
- `http://localhost:5173/*`

## 4) Create realm roles

Create realm roles used by backend authorization:
- `admin`
- `team_lead`
- `employee`

## 5) Create users

Create test users and assign roles:
- `alice.admin` → role `admin`
- `tom.lead` → role `team_lead`
- `emma.employee` → role `employee`

## 6) Link to internal users

Each Keycloak user has a UUID `sub` claim in access tokens.
The backend maps this claim to `users.keycloak_user_id`.

Create matching users in Zytlog DB with the same `keycloak_user_id` value.

## 7) Verify OIDC metadata

Realm issuer:
- `http://localhost:8080/realms/zytlog`

JWKS endpoint:
- `http://localhost:8080/realms/zytlog/protocol/openid-connect/certs`
