# Contributing

## Voraussetzungen

- Docker + Docker Compose
- Python 3.12
- Node 22+
- Git

## Lokales Setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
cd backend && alembic upgrade head
python -m backend.scripts.seed_demo  # optional: Demo-Daten
```

Lokale URLs:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- OpenAPI Docs: http://localhost:8000/docs
- Keycloak: http://localhost:8080

Alternativ ohne Docker — siehe `README.md`.

## Backend

### Tests ausführen

```bash
cd backend
pip install -e ".[dev]"
pytest
```

Tests laufen gegen eine In-Memory-SQLite-Datenbank und benötigen keine laufenden externen Services.

### Neue Migration erstellen

```bash
cd backend
alembic revision --autogenerate -m "beschreibung_der_aenderung"
```

Migrations-Dateien werden unter `backend/migrations/versions/` abgelegt. Namenskonvention: `YYYYMMDD_NNNN_kurzbeschreibung.py`. Vor dem Commit prüfen, ob die generierte Migration korrekt ist — Autogenerate erkennt nicht alle Änderungen zuverlässig (z.B. Check-Constraints, benutzerdefinierte Typen).

Migration anwenden:

```bash
alembic upgrade head
```

### Code-Struktur

```
backend/
├── api/v1/endpoints/   # HTTP-Handler (dünn: nur Request/Response)
├── services/           # Business-Logik
├── repositories/       # Datenbankzugriff (SQLAlchemy)
├── models/             # ORM-Modelle
├── schemas/            # Pydantic-Schemas (Request/Response)
└── core/auth/          # JWT-Validierung, Auth-Kontext, Rollenprüfung
```

Neue Features folgen diesem Muster:
1. Model in `models/`
2. Repository-Methoden in `repositories/`
3. Business-Logik in `services/`
4. Pydantic-Schemas in `schemas/`
5. Endpoint in `api/v1/endpoints/`, im Router registrieren (`api/v1/router.py`)

### Rollenprüfung

Auth-Abhängigkeiten aus `backend/core/auth/dependencies.py` verwenden:

```python
from backend.core.auth import require_authenticated_user, require_admin, require_system_admin

@router.post("/", ...)
def create_something(context: AuthContext = Depends(require_admin)):
    ...
```

Übersicht aller Rollen und Berechtigungen: `docs/security/rbac-matrix.md`.

## Frontend

### Entwicklungsserver

```bash
cd frontend
npm install
npm run dev
```

### Code-Struktur

```
frontend/src/
├── pages/      # Seitenkomponenten (eine Datei pro Route)
├── components/ # Wiederverwendbare UI-Komponenten
├── hooks/      # React Query Hooks (Datenfetching)
├── api/        # Typisierter API-Client
├── auth/       # Keycloak-Provider, Session-Kontext
└── types/      # Gemeinsame TypeScript-Typen
```

Neuer API-Endpunkt einbinden:
1. Typen in `src/types/` definieren
2. API-Funktion in `src/api/` anlegen
3. React Query Hook in `src/hooks/` erstellen
4. Hook in der Komponente/Page verwenden

## Branching

- `main` ist der stabile Branch
- Feature-Branches: `feat/<kurzbeschreibung>`
- Fix-Branches: `fix/<kurzbeschreibung>`
- Dokumentation: `docs/<kurzbeschreibung>`

## Commit-Nachrichten

Konvention: `<typ>: <kurzbeschreibung>` (Englisch oder Deutsch)

| Typ | Wann |
|---|---|
| `feat` | Neue Funktion |
| `fix` | Fehlerbehebung |
| `docs` | Nur Dokumentation |
| `refactor` | Keine neue Funktion, kein Bugfix |
| `test` | Tests hinzufügen oder korrigieren |
| `chore` | Build, Dependencies, CI |

Beispiele:
```
feat: add absence export endpoint
fix: correct daily target calculation for half-day absences
docs: document RBAC matrix
```

## Pull Requests

- PR-Titel folgt der Commit-Konvention
- Beschreibung erklärt das "Warum", nicht nur das "Was"
- Jeder PR sollte Tests enthalten, wenn neue Logik hinzugefügt wird
- Migrations immer zusammen mit dem zugehörigen Model/Schema-Change einreichen

## Fachliche Dokumentation

Änderungen an Kernkonzepten (Berechnungslogik, Rollenmodell, Kalendermodell) müssen die entsprechenden Dokumente in `docs/` aktuell halten:

| Bereich | Dokument |
|---|---|
| Arbeitszeitmodelle, Jahres-Sollzeit | `docs/business-working-time-model.md` |
| Tageskonten, Capture-Status | `docs/business-calendar-model.md` |
| Absenzen | `docs/business-absences.md` |
| Feiertage | `docs/business-holidays.md`, `docs/business-holiday-sets.md` |
| Arbeitsfreie Zeiträume | `docs/business-non-working-periods.md` |
| Berechnungsengine | `docs/technical-calculation-engine.md` |
| Rollen & Berechtigungen | `docs/security/rbac-matrix.md` |
