# Zytlog Frontend

Frontend foundation for Zytlog built with React + TypeScript + Vite.

## Stack

- React 19
- React Router
- TanStack Query
- Typed API client layer
- Nord-inspired theme tokens and app shell

## Run

```bash
cd frontend
npm install
npm run dev
```

Configure API endpoint via:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Structure

- `src/app`: app bootstrapping, router, protected routes
- `src/auth`: auth provider and Keycloak integration seam
- `src/layout`: shell layout (sidebar, topbar, content region)
- `src/pages`: route pages (Dashboard, My Time, Day/Week/Month/Year, Employees, Working Time Models)
- `src/api`: API client + endpoint functions
- `src/components`: reusable UI blocks and table foundation
- `src/hooks`: TanStack Query hooks and mutations
- `src/theme`: theme tokens and global styles
- `src/types`: API response types
