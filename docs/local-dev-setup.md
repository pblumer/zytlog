# Local Development Setup (Docker Compose)

This guide describes a reproducible local setup for zytlog (Frontend + Backend + Keycloak + Postgres) without machine-specific defaults.

## 1) Prerequisites

- Docker Engine + Docker Compose plugin
- Git

Optional (LAN testing): local DNS or /etc/hosts entry for your chosen dev host.

## 2) Default local start (localhost)

```bash
git clone <repo-url>
cd zytlog
docker compose up -d
```

Default endpoints:
- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health
- Keycloak realm metadata: http://localhost:8080/realms/zytlog/.well-known/openid-configuration

## 3) Initialize backend database (required)

After fresh startup, run migrations and seed demo data:

```bash
docker compose exec -T backend bash -lc "alembic -c backend/alembic.ini upgrade head"
docker compose exec -T backend bash -lc "PYTHONPATH=/app python backend/scripts/seed_demo.py"
```

Demo users:
- sysadmin@demo.local / sysadmin
- admin@demo.local / admin
- employee@demo.local / employee

## 4) Non-localhost setup (custom dev host/IP)

Preferred: copy `.env.example` to `.env` and edit values:

```bash
cp .env.example .env
# edit .env with your host/IP values
```

If you prefer shell exports, override compose variables before startup:

```bash
export DEV_VITE_API_BASE_URL="http://<your-host>:8000/api/v1"
export DEV_VITE_KEYCLOAK_URL="http://<your-host>:8080"
export DEV_KEYCLOAK_ISSUER="http://<your-host>:8080/realms/zytlog"
export DEV_CORS_ALLOWED_ORIGINS="http://<your-host>:5173,http://localhost:5173,http://127.0.0.1:5173"

docker compose up -d
```

Notes:
- Backend validates token issuer against DEV_KEYCLOAK_ISSUER.
- Backend CORS is configured from DEV_CORS_ALLOWED_ORIGINS.
- Frontend API/Keycloak URLs come from DEV_VITE_* vars.

## 5) Day-to-day workflow

```bash
docker compose up -d
docker compose down

docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f keycloak
```

## 6) Troubleshooting

### A) Login loop or white screen after Keycloak redirect

Usually CORS preflight failure (`OPTIONS /api/v1/me`).

Check:
```bash
docker compose logs --tail=200 backend
```

Fix:
- Ensure DEV_CORS_ALLOWED_ORIGINS contains the exact frontend origin in use.

### B) Redirected to Unauthorized (tenant context)

Common causes:
1) DB not initialized (missing tables)
2) Issuer mismatch (token `iss` != backend expected issuer)

Fix:
- Run migrations + seed (section 3)
- Ensure DEV_KEYCLOAK_ISSUER matches the URL used by browser tokens

### C) Keycloak login succeeds but app still fails

Verify Keycloak client `zytlog-frontend` includes your frontend origin:
- Redirect URI: `http://<your-host>:5173/*`
- Web Origin: `http://<your-host>:5173`

## 7) Full reset (clean local state)

Warning: removes local DB volumes.

```bash
docker compose down -v
docker compose up -d
docker compose exec -T backend bash -lc "alembic -c backend/alembic.ini upgrade head"
docker compose exec -T backend bash -lc "PYTHONPATH=/app python backend/scripts/seed_demo.py"
```

## 8) Scope and safety

- These settings are for local Docker Compose development only.
- Production deployment must use its own explicit environment and domain configuration.
- Do not reuse DEV_* defaults for production.