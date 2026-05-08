# RBAC-Matrix

Übersicht über alle API-Endpunkte und die jeweils erforderliche Rolle.

## Rollenmodell

| Rolle | Beschreibung |
|---|---|
| `employee` | Normaler Mitarbeiter; kann eigene Zeiterfassung und Reports einsehen |
| `team_lead` | Wie `employee`; technisch vorgesehen, aktuell keine eigenständige Fachrolle ausgebaut |
| `admin` | Tenant-Admin; kann Stammdaten verwalten und auf alle Mitarbeiterdaten des Tenants zugreifen |
| `system_admin` | Systemweiter Administrator; kann Tenants und Systembenutzer verwalten; hat implizit alle Admin-Rechte |

**Vererbung:** `require_admin` erlaubt `admin` und `system_admin`. `require_system_admin` erlaubt nur `system_admin`.

## Legende

| Symbol | Bedeutung |
|---|---|
| ✅ | Zugriff erlaubt |
| ✅ (eigen) | Nur eigene Daten |
| ✅ (tenant) | Alle Daten im eigenen Tenant |
| ❌ | Kein Zugriff (403) |

---

## Authentifizierung

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /api/v1/me` | ✅ | ✅ | ✅ | ✅ |

---

## Zeiterfassung (`/api/v1/time-stamps`)

| Endpoint | employee | team_lead | admin | system_admin | Hinweis |
|---|---|---|---|---|---|
| `POST /clock-in` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | |
| `POST /clock-out` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | |
| `GET /my/current-status` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | |
| `GET /my` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | |
| `POST /manual` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | |
| `PATCH /{id}` | ✅ (eigen) | ✅ (eigen) | ✅ (tenant) | ✅ (tenant) | Admin kann fremde Ereignisse bearbeiten |
| `DELETE /{id}` | ✅ (eigen) | ✅ (eigen) | ✅ (tenant) | ✅ (tenant) | Admin kann fremde Ereignisse löschen |

---

## Tageskonten (`/api/v1/daily-accounts`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /my` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |

---

## Reports (`/api/v1/reports`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /my/week` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |
| `GET /my/month` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |
| `GET /my/year` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |

---

## Kalender (`/api/v1/calendar`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /my/month` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |

---

## Export (`/api/v1/exports`)

Alle Export-Endpunkte sind auf eigene Daten beschränkt und für alle authentifizierten Rollen verfügbar.

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /my/day` (CSV) | ✅ | ✅ | ✅ | ✅ |
| `GET /my/week` (CSV) | ✅ | ✅ | ✅ | ✅ |
| `GET /my/month` (CSV) | ✅ | ✅ | ✅ | ✅ |
| `GET /my/year` (CSV) | ✅ | ✅ | ✅ | ✅ |
| `GET /my/day/pdf` | ✅ | ✅ | ✅ | ✅ |
| `GET /my/week/pdf` | ✅ | ✅ | ✅ | ✅ |
| `GET /my/month/pdf` | ✅ | ✅ | ✅ | ✅ |
| `GET /my/year/pdf` | ✅ | ✅ | ✅ | ✅ |

---

## Mitarbeitende (`/api/v1/employees`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` (alle des Tenants) | ✅ | ✅ | ✅ | ✅ |
| `GET /user-options` | ❌ | ❌ | ✅ | ✅ |
| `POST /` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}` | ❌ | ❌ | ✅ | ✅ |

---

## Arbeitszeitmodelle (`/api/v1/working-time-models`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` | ✅ | ✅ | ✅ | ✅ |
| `POST /` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /{id}` | ❌ | ❌ | ✅ | ✅ |

---

## Feiertagssätze (`/api/v1/holiday-sets`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` | ❌ | ❌ | ✅ | ✅ |
| `POST /` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /{id}` | ❌ | ❌ | ✅ | ✅ |

---

## Feiertage (`/api/v1/holidays`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` | ❌ | ❌ | ✅ | ✅ |
| `POST /` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /{id}` | ❌ | ❌ | ✅ | ✅ |

---

## Arbeitsfreie Zeiträume (`/api/v1/non-working-period-sets`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` | ❌ | ❌ | ✅ | ✅ |
| `POST /` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /{id}` | ❌ | ❌ | ✅ | ✅ |
| `GET /{id}/periods` | ❌ | ❌ | ✅ | ✅ |
| `POST /{id}/periods` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /{id}/periods/{period_id}` | ❌ | ❌ | ✅ | ✅ |
| `DELETE /{id}/periods/{period_id}` | ❌ | ❌ | ✅ | ✅ |

---

## Absenzen

### Self-Service (`/api/v1/absences`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /my` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |
| `POST /my` | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) | ✅ (eigen) |

### Admin (`/api/v1/admin/absences`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /` | ❌ | ❌ | ✅ (tenant) | ✅ (tenant) |
| `POST /` | ❌ | ❌ | ✅ (tenant) | ✅ (tenant) |
| `PATCH /{id}` | ❌ | ❌ | ✅ (tenant) | ✅ (tenant) |
| `DELETE /{id}` | ❌ | ❌ | ✅ (tenant) | ✅ (tenant) |

---

## OpenHolidays-Import (`/api/v1/admin/openholidays`)

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /openholidays/countries` | ❌ | ❌ | ✅ | ✅ |
| `GET /openholidays/languages` | ❌ | ❌ | ✅ | ✅ |
| `GET /openholidays/subdivisions` | ❌ | ❌ | ✅ | ✅ |
| `POST /holiday-sets/{id}/import/openholidays/preview` | ❌ | ❌ | ✅ | ✅ |
| `POST /holiday-sets/{id}/import/openholidays/commit` | ❌ | ❌ | ✅ | ✅ |

---

## Systemverwaltung (`/api/v1/system`)

Ausschliesslich `system_admin`. Alle anderen Rollen erhalten 403.

| Endpoint | employee | team_lead | admin | system_admin |
|---|---|---|---|---|
| `GET /tenants` | ❌ | ❌ | ❌ | ✅ |
| `POST /tenants` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /tenants/{id}` | ❌ | ❌ | ❌ | ✅ |
| `GET /users` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /users/{id}` | ❌ | ❌ | ❌ | ✅ |

---

## Implementierungsdetails

Die Rollenprüfung erfolgt über FastAPI-Abhängigkeiten in `backend/core/auth/dependencies.py`:

```python
require_authenticated_user  # employee, team_lead, admin, system_admin
require_admin               # admin, system_admin
require_system_admin        # system_admin
require_team_lead_or_admin  # team_lead, admin, system_admin (aktuell nicht aktiv genutzt)
```

Tenant-Isolation: Jeder authentifizierte Request ist über `context.tenant_id` auf den eigenen Tenant beschränkt. Die Isolation wird im Service-Layer durch parameterisierte Queries sichergestellt — es gibt keine Möglichkeit, auf Daten anderer Tenants zuzugreifen, auch nicht als `admin`.

`system_admin` operiert systemweit (kein Tenant-Scope) und hat ausschliesslich Zugriff auf die Endpunkte unter `/api/v1/system/`.
