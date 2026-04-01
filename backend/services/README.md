# Backend Services

Der Service-Layer orchestriert tenant-scoped Use-Cases, Validierungen und zentrale Berechnungslogik.

## Kernservices

- `time_tracking_service.py`
  - Clock-in/Clock-out, Sequenzvalidierung, manuelle Erfassung, Korrektur/Löschen unter Rollenregeln.

- `daily_account_service.py`
  - Zentrale Tageskonto-Berechnung (`target_minutes`, `actual_minutes`, `break_minutes`, `balance_minutes`, Status, Kontext).
  - Enthält annual-target-basierte Sollzeitlogik inkl. Feiertag, Absenzkontext und non-working periods.

- `reporting_service.py`
  - Week/Month/Year-Overviews auf Basis der Tageskonten.
  - Aggregiert Totals und Statuszählungen.

- `calendar_service.py`
  - Liefert kalenderoptimierte Monatsdarstellung aus dem Monatsreport.
  - Mappt Tagesstatus (`empty` -> `no_data`) und reicht Kontexte durch.

- `holiday_service.py`, `holiday_set_service.py`, `openholidays_import_service.py`
  - Feiertagsdomäne inkl. manueller OpenHolidays-Importstrecke (Preview/Commit).

- `absence_service.py`
  - Stage-1-Absenzlogik (Validierung + Kontextauflösung).

- `non_working_period_set_service.py`
  - Verwaltung und Auflösung arbeitsfreier Zeiträume und deren Tagesabbildung.

## Prinzip

Fachlogik wird im Backend zentral berechnet und in mehrere Endpunkte/Sichten wiederverwendet; das Frontend konsumiert konsistente Ergebnisdaten.

Siehe auch:
- `docs/technical-calculation-engine.md`
