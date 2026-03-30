# Zytlog — Architecture Foundation (MVP Baseline)

Zytlog is a tenant-aware web time tracking platform. This initial baseline focuses on **clean architecture, core domain model, and extensible project setup** without implementing business workflows yet.

## 1) Architecture Overview

### Frontend
- **Stack:** React + TypeScript + Vite
- **Goal:** Feature-first UI modules, reusable components, API adapter boundary, and centralized theme tokens.
- **Design direction:** Nord-inspired token system prepared for future advanced grids and inline editing.

### Backend
- **Stack:** FastAPI + Python + SQLAlchemy 2.x + Pydantic + Alembic
- **Goal:** Layered architecture with explicit tenant scoping and integration seams for Keycloak.
- **Layers:**
  - `api/`: HTTP endpoints and request wiring
  - `schemas/`: API contracts (Pydantic)
  - `services/`: business use-case orchestration (future)
  - `repositories/`: persistence abstractions (future)
  - `models/`: SQLAlchemy ORM entities
  - `db/`: base metadata + session handling

### Database
- **PostgreSQL** as the primary relational store.
- Tenant scoping included at entity level for all business data.

### Auth (Integration points only)
- Keycloak integration planned via:
  - backend config placeholders (`core/config.py`)
  - frontend auth seam (`frontend/api/auth.ts`)
  - infrastructure folder for realm/client bootstrap assets.

---

## 2) Full Project Structure

```text
zytlog/
├── backend/
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── __init__.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── migrations/
│   │   ├── README.md
│   │   └── versions/
│   │       └── .gitkeep
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── employee.py
│   │   ├── working_time_model.py
│   │   ├── time_stamp_event.py
│   │   └── daily_time_account.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── README.md
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   └── tenant.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── README.md
│   ├── main.py
│   └── __init__.py
├── frontend/
│   ├── api/
│   │   ├── auth.ts
│   │   └── client.ts
│   ├── components/
│   │   └── README.md
│   ├── features/
│   │   └── README.md
│   ├── layout/
│   │   └── AppLayout.tsx
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   └── index.ts
│   ├── theme/
│   │   ├── index.ts
│   │   └── tokens.ts
│   └── README.md
├── infrastructure/
│   └── keycloak/
│       └── README.md
├── docker-compose.yml
└── README.md
```

---

## 3) Core Domain Model (Tenant-aware)

### Tenant
- `id`
- `name`
- `slug` (unique)
- `is_active`
- timestamps

**Relations:**
- one-to-many with `User`, `Employee`, `WorkingTimeModel`, `TimeStampEvent`, `DailyTimeAccount`

### User (auth-linked identity)
- `id`
- `tenant_id`
- `email` (unique)
- `full_name`
- `keycloak_subject` (unique external identity link)
- `is_admin`
- timestamps

**Relations:**
- many-to-one to `Tenant`
- one-to-one to `Employee`

### Employee (workforce profile)
- `id`
- `tenant_id`
- `user_id` (one-to-one)
- `working_time_model_id` (nullable assignment)
- `employee_number`
- `status` (`active`/`inactive`)
- `hire_date`
- timestamps

**Relations:**
- many-to-one to `Tenant`
- one-to-one to `User`
- many-to-one to `WorkingTimeModel`
- one-to-many to `TimeStampEvent`, `DailyTimeAccount`

### WorkingTimeModel
- `id`
- `tenant_id`
- `name`
- `model_type` (`fixed`/`flexible`)
- `expected_daily_hours`
- `break_minutes_default`
- `is_active`
- timestamps

**Relations:**
- many-to-one to `Tenant`
- one-to-many to `Employee`

### TimeStampEvent
- `id`
- `tenant_id`
- `employee_id`
- `event_type` (`clock_in`, `clock_out`, `break_start`, `break_end`)
- `event_at` (timezone-aware)
- `source` (e.g. web/mobile/import)
- timestamps

**Relations:**
- many-to-one to `Tenant`
- many-to-one to `Employee`

### DailyTimeAccount
- `id`
- `tenant_id`
- `employee_id`
- `account_date`
- `planned_minutes`
- `worked_minutes`
- `break_minutes`
- `delta_minutes`
- `balance_minutes`
- timestamps

**Relations:**
- many-to-one to `Tenant`
- many-to-one to `Employee`

---

## 4) Backend Model Examples (SQLAlchemy)

Concrete SQLAlchemy 2.x model examples are implemented in:
- `backend/models/tenant.py`
- `backend/models/user.py`
- `backend/models/employee.py`
- `backend/models/working_time_model.py`
- `backend/models/time_stamp_event.py`
- `backend/models/daily_time_account.py`

Shared persistence primitives:
- `backend/db/base.py` (`Base`, `TimestampMixin`)
- `backend/db/session.py` (`engine`, `SessionLocal`)

---

## 5) Frontend Structure and Design Plan

- `theme/tokens.ts`: source of truth for Nord tokens, spacing, and typography.
- `theme/index.ts`: app theme composition layer.
- `features/`: reserved for feature-based modules (`time-tracking`, `reporting`, etc.).
- `api/client.ts`: centralized fetch client seam.
- `api/auth.ts`: Keycloak integration seam for token and tenant claim handling.

### Data Grid Readiness (planned)
- Keep table abstractions in `features/*/components` to avoid global coupling.
- Store column definitions close to feature modules.
- Add `features/*/hooks` for server-side pagination/filtering later.
- Reuse theme tokens for row states, inline edit affordances, and status badges.

---

## 6) Docker Compose Placeholder

A minimal local orchestration placeholder is provided in `docker-compose.yml` with:
- `db` (PostgreSQL)
- `backend` (Python container placeholder)
- `frontend` (Node container placeholder)
- `keycloak` (dev mode)

This is intentionally non-production and designed to be expanded in the next implementation phase.

---

## 7) Setup (Foundation Phase)

1. Start infrastructure placeholders:
   ```bash
   docker compose up -d
   ```
2. Extend backend image/command to run FastAPI with Uvicorn.
3. Scaffold Vite app in `frontend/` and wire `api/client.ts`.
4. Add Alembic `env.py` and first migration from `backend.models` metadata.
5. Implement Keycloak realm/client bootstrap in `infrastructure/keycloak/`.

---

## Extensibility Notes

The structure intentionally leaves clean seams for:
- **Absences** (new entity + service + repository)
- **Approvals** (workflow service + state machine)
- **Audit logs** (cross-cutting append-only model and middleware hooks)

Because tenant scoping is modeled directly in core entities, later features can inherit isolation constraints consistently.

## Backend quickstart (foundation)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
cd ..
alembic -c backend/alembic.ini upgrade head
uvicorn backend.main:app --reload
```

Key API routes:
- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/me`
- `GET|POST /api/v1/employees`
- `GET|POST /api/v1/working-time-models`
