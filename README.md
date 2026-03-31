# Zytlog MVP

Zytlog is a **tenant-aware web time-tracking MVP** for small teams. It supports authenticated clock-in/clock-out tracking, derived daily time accounts, period reporting (week/month/year), correction flow, and CSV/PDF exports.

This repository is focused on a demo-ready MVP baseline that is practical to run locally and safe to extend.

## MVP scope (current)

Included:
- FastAPI backend with tenant-scoped data access.
- Keycloak-ready JWT authentication and role checks.
- Employee time-stamp tracking (`clock_in`, `clock_out`, breaks).
- Derived daily accounts and status calculations.
- Weekly / monthly / yearly personal reporting.
- Day/week/month/year CSV + PDF export endpoints.
- Correction endpoint for timestamp/comment updates with sequence validation.
- React + Vite frontend app shell with DataGrid-based reporting pages.
- Annual/weekly working-time foundations with weekday work-pattern logic.
- Admin management for working-time models (create, edit, safe delete with assignment protection).
- Role-aware primary navigation (admin-focused menu vs employee self-service menu).

Out of scope (not implemented here):
- Approval workflows.
- Absence management.
- Full audit trail module.
- Production-grade SSO provisioning automation.

## Business rules: working time model and daily target time

The core Fachlichkeit for annual/weekly target-time foundations is documented in:

- `docs/business-working-time-model.md`

This includes:
- meaning of `WorkingTimeModel` and `employment_percentage`
- model vs employee weekday resolution
- day-scoped target-minute calculation
- behavior before `entry_date` / after `exit_date`
- current scope of `annual_target_hours`
- explicit non-scope (vacation/sickness/holidays, etc.)

## Architecture overview

### Backend
- **Framework**: FastAPI + SQLAlchemy + Alembic.
- **Auth**: JWT validation via Keycloak JWKS.
- **Tenant model**: user -> tenant mapping in DB; all business data is tenant-scoped.
- **Business services**: time tracking, daily account derivation, reporting, export.

### Frontend
- **Framework**: React 19 + TypeScript + Vite.
- **Data/state**: TanStack Query + typed API client.
- **Routing/auth shell**: protected routes and app shell layout.
- **Primary table UI**: `DataGrid` in `frontend/src/components/DataGrid.tsx`.

## Repository structure

```text
backend/                  FastAPI app, services, repositories, models, tests
frontend/                 React app
frontend/src/             Active frontend source tree (source of truth)
infrastructure/keycloak/  Local Keycloak setup notes
docker-compose.yml        Local multi-service startup
```

> Note: Legacy duplicate frontend folders outside `frontend/src/*` were removed to avoid confusion. Use `frontend/src/*` as the single active tree.

## Role model and tenant-aware behavior

Roles:
- `employee`
- `team_lead`
- `admin`

Tenant behavior:
- Every internal user belongs to exactly one tenant.
- API access is scoped by tenant from auth context.
- Admin-only operations (e.g., employee/model create) require `admin`.
- Working time models can be edited by admins and deleted only when unassigned; otherwise the API returns a conflict message.
- Time-stamp correction allows tenant admins for all tenant events, while employees/team leads can only edit their own events.

## Key API flows

Authentication + context:
- `GET /api/v1/me`

Time tracking:
- `POST /api/v1/time-stamps/clock-in`
- `POST /api/v1/time-stamps/clock-out`
- `GET /api/v1/time-stamps/my?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/v1/time-stamps/my/current-status`
- `PATCH /api/v1/time-stamps/{time_stamp_id}`

Daily account + reports:
- `GET /api/v1/daily-accounts/my?date=YYYY-MM-DD`
- `GET /api/v1/reports/my/week?year=YYYY&week=WW`
- `GET /api/v1/reports/my/month?year=YYYY&month=MM`
- `GET /api/v1/reports/my/year?year=YYYY`

Exports:
- Day: `GET /api/v1/exports/my/day` + `/pdf`
- Week: `GET /api/v1/exports/my/week` + `/pdf`
- Month: `GET /api/v1/exports/my/month` + `/pdf`
- Year: `GET /api/v1/exports/my/year` + `/pdf`

Working time models (admin):
- `GET /api/v1/working-time-models`
- `POST /api/v1/working-time-models`
- `PATCH /api/v1/working-time-models/{model_id}`
- `DELETE /api/v1/working-time-models/{model_id}` (blocked with `409` if still assigned to employees)

## Local development setup

## 1) Prerequisites
- Docker + Docker Compose
- Python 3.12+ (for local backend outside Docker)
- Node 22+ and npm (for local frontend outside Docker)

## 2) Environment files

Copy examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## 3) Start full stack with Docker Compose

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Keycloak: http://localhost:8080
- PostgreSQL: localhost:5432

## 4) Apply DB migrations

From repository root:

```bash
cd backend
alembic upgrade head
```

(You can run this on host Python env or inside backend container.)

## 5) Seed demo data (recommended for demos)

```bash
python -m backend.scripts.seed_demo
```

This creates (idempotently):
- one demo tenant (`demo-co`)
- one admin user mapping (`admin@demo.local`)
- one employee user mapping (`employee@demo.local`)
- one working time model
- sample timestamp events for current and previous day

### Keycloak note for local demo

If your Keycloak users use different subject IDs, update the seeded `users.keycloak_user_id` values or create matching users in Keycloak so JWT `sub` matches DB records.

Detailed Keycloak bootstrap remains in:
- `infrastructure/keycloak/README.md`

## Alternative: run backend/frontend directly (without Compose)

### Backend

```bash
cd backend
pip install -e .
alembic upgrade head
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Development checks

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm run check
npm run build
```

## Known MVP limitations

- Auth flow is Keycloak-ready but still demo-oriented in local setup.
- No dedicated approval pipeline for corrections yet.
- No absence planning/calendar module.
- No long-term audit/event sourcing stream.
- Local compose installs dependencies at container start (optimized for simplicity, not production image performance).

## Frontend consistency and UX notes

Current frontend hardening includes:
- consistent empty-state handling across day/week/month/year pages
- consistent report export action placement in page headers
- clearer export and correction failure messages
- DataGrid-first table usage
- admin navigation intentionally reduced to admin-relevant items (`Employees`, `Working Time Models`) while self-service pages remain employee-focused in the current MVP

## Demo startup sequence (quick)

1. `docker compose up --build`
2. `cd backend && alembic upgrade head`
3. `python -m backend.scripts.seed_demo`
4. Configure Keycloak realm/users (see `infrastructure/keycloak/README.md`)
5. Open http://localhost:5173 and sign in with a mapped user
