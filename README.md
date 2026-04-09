# Zytlog MVP

Zytlog ist eine **tenant-fähige Web-Anwendung für Zeiterfassung** mit jährlicher Sollzeitlogik, Tageskonten, Kalenderkontexten und periodischem Reporting.

Dieses Repository dokumentiert den aktuell implementierten MVP-Stand (Backend + Frontend) und dient als stabile Basis für fachliche Erweiterungen.

## Schnellstart

1. Umgebungsdateien kopieren:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Stack starten:

```bash
docker compose up --build
```

3. Migrationen ausführen:

```bash
cd backend
alembic upgrade head
```

4. Optional Demo-Daten laden (empfohlen für reproduzierbare lokale Tests):

```bash
python -m backend.scripts.seed_demo
```

Demo identities (Keycloak + DB mapping):
- sysadmin@demo.local / sysadmin (role: system_admin)
- admin@demo.local / admin (role: admin)
- employee@demo.local / employee (role: employee)

Lokale URLs:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- Keycloak: http://localhost:8080

## Keycloak-Persistenz (lokal/dev)

- Keycloak läuft lokal mit einer **eigenen Postgres-Datenbank** (`keycloak-db` Service in `docker-compose.yml`).
- Die Datenbank wird im Named Volume `keycloak_postgres_data` gespeichert.
- Realm-Import läuft über `start-dev --import-realm` mit `keycloak/realm-import/zytlog-realm.json`.
- Der Import ist für den Initial-Setup gedacht: Wenn der Realm bereits in der DB existiert, wird er nicht bei jedem Neustart neu überschrieben.

Was bleibt nach `docker compose down` + `docker compose up` erhalten:
- Realms
- Benutzer
- Clients / Konfiguration

Keycloak-Daten **bewusst zurücksetzen**:

```bash
docker compose down
docker volume rm zytlog_keycloak_postgres_data
docker compose up -d keycloak keycloak-db
```

## Fachliche Kernkonzepte

- **Jahres-Sollzeit als führende Grösse** (`annual_target_hours`) inkl. Verteilung auf target-bearing Arbeitstage.
- **Kalenderkontexte je Tag**: Feiertag, Absenz, arbeitsfreier Zeitraum.
- **Capture-Status getrennt vom Tageskontext**: `complete`, `incomplete`, `invalid`, `empty`.
- **Vorarbeitungs-Effekt**: Feiertage und arbeitsfreie Zeiträume reduzieren target-bearing Tage; die Jahres-Sollzeit bleibt konstant.

Detaillierte Fachdokumente unter `docs/`:
- `docs/business-working-time-model.md`
- `docs/business-calendar-model.md`
- `docs/business-month-view.md`
- `docs/business-absences.md`
- `docs/business-holiday-sets.md`
- `docs/business-holidays.md`
- `docs/business-non-working-periods.md`
- `docs/frontend-views.md`
- `docs/technical-calculation-engine.md`

## Rollen- und Tenant-Modell

Implementierte Rollen (Systemstand):
- `employee`
- `team_lead`
- `admin`
- `system_admin`

Aktueller MVP-Verhaltensstand:
- Systemweite Verwaltungsendpunkte sind auf `system_admin` eingeschränkt.
- Tenant-lokale Admin-Endpunkte erlauben `admin` und `system_admin`.
- Self-Service-Endpunkte sind für authentifizierte Nutzer verfügbar.
- Für Korrektur-/Löschvorgänge gilt derzeit fachlich: `admin` kann tenant-weit, Nicht-Admins nur eigene Ereignisse.
- Die Rolle `team_lead` ist technisch weiterhin Teil des Rollenmodells, wird im aktuellen UI/Use-Case aber nicht als eigenständige Fachrolle ausgebaut.

Tenant-Regeln:
- Jeder interne Nutzer gehört genau einem Tenant.
- Fachdatenzugriffe sind tenant-scoped.
- Mitarbeitenden-Verwaltung in Zytlog ist Fachprofil-Verwaltung (nicht vollständige Identity-Verwaltung in Keycloak).

## Architekturüberblick

### Backend
- FastAPI + SQLAlchemy + Alembic.
- JWT-Validierung via Keycloak (JWKS).
- Service-Layer für Zeitbuchung, Tageskonten, Reporting, Kalender und Exporte.
- Zentrale Berechnungslogik im Backend; Frontend nutzt dieselben API-Ergebnisse in allen Sichten.

### Frontend
- React 19 + TypeScript + Vite.
- TanStack Query + typisierte API-Endpunkte.
- Kalender-/Report-Sichten: Dashboard, My Time, Day, Week, Month, Year.
- Admin-Sichten für Mitarbeitende, Arbeitszeitmodelle, Feiertagssätze, Feiertage, arbeitsfreie Zeiträume und Absenzen.

## API-Kernflüsse (Auszug)

Authentifizierung/Kontext:
- `GET /api/v1/me`

Zeiterfassung:
- `POST /api/v1/time-stamps/clock-in`
- `POST /api/v1/time-stamps/clock-out`
- `GET /api/v1/time-stamps/my?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/v1/time-stamps/my/current-status`
- `PATCH /api/v1/time-stamps/{time_stamp_id}`

Tageskonto, Kalender, Reports:
- `GET /api/v1/daily-accounts/my?date=YYYY-MM-DD`
- `GET /api/v1/calendar/my/month?year=YYYY&month=MM`
- `GET /api/v1/reports/my/week?year=YYYY&week=WW`
- `GET /api/v1/reports/my/month?year=YYYY&month=MM`
- `GET /api/v1/reports/my/year?year=YYYY`

Admin-Domänen:
- Working Time Models: `/api/v1/working-time-models`
- Holiday Sets + Holidays: `/api/v1/holiday-sets`, `/api/v1/holidays`
- Non-Working Period Sets: `/api/v1/non-working-period-sets`
- Absences: `/api/v1/my/absences`, `/api/v1/admin/absences`
- System Administration: `/api/v1/system/tenants`, `/api/v1/system/users`

OpenHolidays:
- Manuelle Preview/Commit-Importstrecke unter `/api/v1/admin/.../openholidays/...`.
- OpenHolidays ist **Importquelle**, keine Laufzeit-Abhängigkeit für Tagesberechnung.

## Repository-Struktur

```text
backend/                  FastAPI App, Services, Repositories, Modelle, Tests
frontend/                 React App
docs/                     Fachliche und technische Projektdokumentation
infrastructure/keycloak/  Hinweise für lokale Keycloak-Konfiguration
docker-compose.yml        Lokales Multi-Service-Setup
```

## Alternative: ohne Docker Compose

Backend:

```bash
cd backend
pip install -e .
alembic upgrade head
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
