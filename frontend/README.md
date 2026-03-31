# Zytlog Frontend

React + TypeScript + Vite frontend for the Zytlog MVP.

## Active source tree

Use **`frontend/src/*`** as the source of truth.

Legacy duplicate frontend folders outside `src` were removed during MVP cleanup to keep onboarding clear.

## Stack

- React 19
- React Router
- TanStack Query
- Typed API client layer
- DataGrid-first table/report UI

## Run locally

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Default local frontend URL: http://localhost:5173

## Environment

`.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
# VITE_DEV_BEARER_TOKEN=<optional_dev_token>
```

## Structure

- `src/app`: app bootstrap, router, protected route flow
- `src/auth`: auth provider and auth state
- `src/layout`: shell layout (sidebar, topbar, content)
- `src/pages`: route pages (dashboard, day/week/month/year, admin lists)
- Holiday set admin page includes manual OpenHolidays import with preview + commit into a selected Feiertagssatz.
- `src/api`: API client + endpoint functions
- `src/components`: reusable page/table UI primitives
- `src/hooks`: query hooks and mutations
- `src/theme`: design tokens + global styles
- `src/types`: API types
