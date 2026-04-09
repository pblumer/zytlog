# Local Development Setup (Docker Compose)

This guide documents a reproducible local setup for `zytlog` with full auth flow (Frontend + Backend + Keycloak + Postgres).

## 1) Prerequisites

- Docker Engine + Docker Compose plugin
- Git
- A host name that matches your frontend/keycloak URLs (recommended)

Recommended local host mapping (example):

```bash
# /etc/hosts
192.168.1.203 pi-server-03.home
```

If you use a different hostname/IP, update all related config consistently (see Troubleshooting section).

## 2) Clone and start services

```bash
git clone <repo-url>
cd zytlog
docker compose up -d
```

Check container status:

```bash
docker compose ps
```

Expected services:
- `frontend` on `:5173`
- `backend` on `:8000`
- `keycloak` on `:8080`
- `db` and `keycloak-db`

## 3) Initialize backend database (required)

Important: backend tables are not guaranteed to exist after a fresh start unless migrations are applied.

Run migrations:

```bash
docker compose exec -T backend bash -lc "alembic -c backend/alembic.ini upgrade head"
```

Seed demo data:

```bash
docker compose exec -T backend bash -lc "PYTHONPATH=/app python backend/scripts/seed_demo.py"
```

This creates/updates demo tenant and users:
- `sysadmin@demo.local` / `sysadmin`
- `admin@demo.local` / `admin`
- `employee@demo.local` / `employee`

## 4) Open the app

- Frontend: `http://pi-server-03.home:5173`
- Keycloak realm metadata: `http://pi-server-03.home:8080/realms/zytlog/.well-known/openid-configuration`
- Backend health: `http://pi-server-03.home:8000/health`

Log in with one of the demo users above.

## 5) Day-to-day developer workflow

Start/stop:

```bash
docker compose up -d
docker compose down
```

Backend logs:

```bash
docker compose logs -f backend
```

Frontend logs:

```bash
docker compose logs -f frontend
```

Keycloak logs:

```bash
docker compose logs -f keycloak
```

## 6) Troubleshooting

### A) Login loop / white screen after Keycloak redirect

Typical cause:
- CORS preflight (`OPTIONS /api/v1/me`) fails with `400`.

Checks:

```bash
docker compose logs --tail=200 backend
```

Fix:
- Ensure backend CORS `allow_origins` includes your actual frontend origin(s), e.g.:
  - `http://localhost:5173`
  - `http://pi-server-03.home:5173`
  - `http://192.168.1.203:5173`

### B) Always redirected to Unauthorized ("not authenticated for this tenant context")

Common causes:
1. Backend DB not initialized (`users` table missing)
2. Backend token issuer mismatch

Checks:
- Backend errors like `relation "users" does not exist`
- `/api/v1/me` returns `401 Invalid or expired token`

Fixes:
1. Run migrations + seed (section 3)
2. Ensure backend issuer matches real token issuer (in compose env):
   - `KEYCLOAK_ISSUER=http://pi-server-03.home:8080/realms/zytlog`

### C) Keycloak login works, but app still fails

Verify Keycloak client `zytlog-frontend` has correct:
- Redirect URIs (e.g. `http://pi-server-03.home:5173/*`)
- Web Origins (e.g. `http://pi-server-03.home:5173`)

### D) Frontend runtime error after login

If you hit an "Unexpected Application Error" in Vite dev mode, inspect frontend logs and browser console first; this is usually a frontend hook/runtime bug and not auth infrastructure.

## 7) Full reset (clean local state)

Warning: removes local DB data.

```bash
docker compose down -v
docker compose up -d
docker compose exec -T backend bash -lc "alembic -c backend/alembic.ini upgrade head"
docker compose exec -T backend bash -lc "PYTHONPATH=/app python backend/scripts/seed_demo.py"
```

## 8) Configuration consistency checklist

When changing hostnames/IPs, keep these in sync:

- Frontend runtime config (`VITE_*` values in compose)
- Backend auth env (`KEYCLOAK_ISSUER`, optionally JWKS URL)
- Backend CORS origins
- Keycloak client redirect URIs + web origins
- Local DNS/hosts entry

If one of these is inconsistent, auth issues are likely.