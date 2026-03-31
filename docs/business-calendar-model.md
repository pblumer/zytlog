# Fachlichkeit: Kalenderkontext (Feiertag, Absenz, Arbeitsfreier Zeitraum)

Stand: 31.03.2026

## Ziel
Dieses Dokument beschreibt die fachliche Trennung der Tageskontexte in Zytlog und deren Wirkung auf die annual-target-basierte Sollzeitlogik.

## Drei getrennte Konzepte

### 1) Feiertag
- Quelle: Feiertagssatz (`HolidaySet`) inkl. optionalem Mitarbeiter-Override.
- Wirkung:
  - `target_minutes = 0`
  - Tag ist **nicht** target-bearing.
- Charakter: kalender-/standortbezogene Regel, nicht personenspezifische Abwesenheit.

### 2) Absenz
- Eigene Domain (`absence`: `vacation` / `sickness`, `full_day` / `half_day_am` / `half_day_pm`).
- Wirkung:
  - Absenz wird als Tageskontext sichtbar gemacht.
  - Capture-Status bleibt getrennt (`complete` / `incomplete` / `invalid` / `empty`).
- Charakter: personenbezogener Tageskontext, kein Feiertag.

### 3) Arbeitsfreier Zeitraum (`non_working_period`)
- Eigene Domain für organisatorisch freie Zeitfenster (z. B. Schulferien für bestimmte Gruppen).
- Modell:
  - `non_working_period_sets`
  - `non_working_periods` (`start_date`, `end_date`, `name`, optionale `category`)
  - optional `employee.non_working_period_set_id`
- Wirkung:
  - `target_minutes = 0` an betroffenen Tagen
  - Tage sind **nicht** target-bearing
  - Jahresarbeitszeit bleibt konstant
- Charakter: organisatorische Arbeitsregel, explizit **keine** Absenz und **kein** Feiertag.

## Wirkung auf annual target logic (Vorarbeitungs-Effekt)

Zytlog verwendet weiterhin `annual_target_hours` als führende Sollgrösse.

Die effektive jährliche Sollzeit wird auf target-bearing Tage verteilt. Wird ein Tag wegen Feiertag oder Arbeitsfrei-Periode target-frei, reduziert sich die Anzahl target-bearing Tage. Dadurch steigt die Sollzeit pro verbleibendem target-bearing Tag (Vorarbeitungs-Effekt), während die Jahresarbeitszeit konstant bleibt.

## API-/UI-Kontext

Tagesbezogene DTOs führen den Kontext getrennt:
- `is_holiday` + `holiday_name`
- `absence`
- `is_in_non_working_period` + `non_working_period_label`

Damit bleiben semantische Grenzen klar und in Day/Month-Ansichten sichtbar.
