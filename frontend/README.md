# Zytlog Frontend

React + TypeScript + Vite Frontend für den Zytlog-MVP.

## Aktiver Source Tree

Verwende **`frontend/src/*`** als Source of Truth.

## Stack

- React 19
- React Router
- TanStack Query
- Typisierte API-Client-Schicht
- DataGrid-basierte Tabellen-/Reporting-Komponenten

## Lokal starten

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Standard-URL lokal: http://localhost:5173

## Environment

`.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
# VITE_DEV_BEARER_TOKEN=<optional_dev_token>
```

## Strukturüberblick

- `src/app`: Bootstrap, Router, Protected Routes
- `src/auth`: Auth Provider + Session-Kontext
- `src/layout`: AppShell (Navigation, Rahmen)
- `src/pages`: Produktseiten (Dashboard, My Time, Day/Week/Month/Year, Admin)
- `src/api`: Endpunkte + API Client
- `src/components`: wiederverwendbare UI-/Tabellenbausteine
- `src/hooks`: Query/Mutation Hooks
- `src/theme`: Tokens + globale Styles
- `src/types`: API-Typen

## Sichtmodell (kurz)

- **Dashboard / My Time**: schneller operativer Einstieg, aktueller Status, kompakte Kalender.
- **Day**: Detail- und Korrekturansicht für Zeitereignisse.
- **Week / Month / Year**: verdichtete Auswertungen mit Status + Tageskontext.
- **Admin-Sichten**: Stammdaten und Regelwerke (Mitarbeitende, Arbeitszeitmodelle, Feiertage, arbeitsfreie Zeiträume, Absenzen).

Für die fachlich-technische Sichtbeschreibung siehe:
- `docs/frontend-views.md`
