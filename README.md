# Zytlog — Architecture Foundation (MVP Baseline)

Zytlog is a tenant-aware web time tracking platform. This baseline now includes a real authentication/authorization foundation around FastAPI + SQLAlchemy + tenant-aware scoping.

## Backend auth foundation

- Bearer JWT validation using Keycloak JWKS.
- Issuer validation (required).
- Optional audience validation.
- Claim extraction (`sub`, `preferred_username`, `email`, roles).
- Internal user mapping through `users.keycloak_user_id`.
- Tenant context derived from internal user (`users.tenant_id`).
- Role-enforcement dependencies:
  - `require_authenticated_user`
  - `require_role(...)`
  - `require_admin`
  - `require_team_lead_or_admin`

## Environment configuration

Set these variables in `backend/.env` (or process env):

```env
DATABASE_URL=postgresql+psycopg://zytlog:zytlog@db:5432/zytlog

AUTH_ENABLED=true
AUTH_DISABLED_FALLBACK_USER_ID=1

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=zytlog
KEYCLOAK_ISSUER=http://localhost:8080/realms/zytlog
KEYCLOAK_JWKS_URL=http://localhost:8080/realms/zytlog/protocol/openid-connect/certs

KEYCLOAK_VERIFY_AUDIENCE=true
KEYCLOAK_AUDIENCE=account
```

Notes:
- `KEYCLOAK_ISSUER` and `KEYCLOAK_JWKS_URL` are optional; they are derived from `KEYCLOAK_URL` + `KEYCLOAK_REALM` if omitted.
- Keep `AUTH_ENABLED=true` in normal development to use real JWT flows.
- `AUTH_ENABLED=false` can be used temporarily for local fallback wiring.

## Protected API behavior

- `GET /api/v1/me`: authenticated user context (`user_id`, `username`, `email`, `role`, `tenant_id`)
- `GET /api/v1/employees`: authenticated users
- `POST /api/v1/employees`: admin only
- `GET /api/v1/working-time-models`: authenticated users
- `POST /api/v1/working-time-models`: admin only
- `GET /api/v1/reports/my/week?year=&week=`: authenticated employee week overview with daily rows and totals
- `GET /api/v1/reports/my/month?year=&month=`: authenticated employee month overview with daily rows and totals
- `GET /api/v1/reports/my/year?year=`: authenticated employee year overview with month rows and annual totals
- `GET /api/v1/exports/my/day?date=` and `GET /api/v1/exports/my/day/pdf?date=`: export day report as CSV/PDF
- `GET /api/v1/exports/my/week?year=&week=` and `GET /api/v1/exports/my/week/pdf?year=&week=`: export week overview as CSV/PDF
- `GET /api/v1/exports/my/month?year=&month=` and `GET /api/v1/exports/my/month/pdf?year=&month=`: export month overview as CSV/PDF
- `GET /api/v1/exports/my/year?year=` and `GET /api/v1/exports/my/year/pdf?year=`: export year overview as CSV/PDF
- `PATCH /api/v1/time-stamps/{time_stamp_id}`: correction endpoint for `timestamp` and `comment`
  - tenant admin can correct any event in their tenant
  - employees/team leads can only correct their own events
  - correction is rejected with `409` if clock-in/clock-out sequence would become invalid
  - daily account/reporting values reflect corrections automatically because accounts are derived from event reads

## Local Keycloak setup

See detailed bootstrap steps in `infrastructure/keycloak/README.md`.

## Docker Compose

```bash
docker compose up -d
```

Includes:
- `db` (PostgreSQL)
- `backend` container scaffold
- `frontend` container scaffold
- `keycloak` (dev mode)
