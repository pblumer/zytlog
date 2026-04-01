# Fachlichkeit: Working-Time-Model (annual target als führende Sollgrösse)

Stand: 01.04.2026

## Ziel dieses Dokuments

Dieses Dokument beschreibt den **aktuell implementierten** Fachstand der Sollzeitlogik in Zytlog.

Kernaussage: `annual_target_hours` ist die einzige führende Sollgrösse. Die tägliche Sollzeit wird daraus zentral im Backend berechnet und in Day/Week/Month/Year sowie Kalenderansichten wiederverwendet.

## 1) Führende Sollgrösse

- `WorkingTimeModel.annual_target_hours` ist verpflichtend und autoritativ.
- Eine getrennte Pflege von Wochenzielstunden ist entfernt.
- `employment_percentage` auf `Employee` skaliert die jährliche Sollzeit.

Formel (vereinfacht):

`effective_annual_minutes = annual_target_hours * 60 * employment_percentage / 100`

## 2) Arbeitsmuster-Auflösung (Modell + Mitarbeiter)

`WorkingTimeModel` liefert das Standard-Wochentagsmuster:
- `default_workday_monday` ... `default_workday_sunday`

`Employee` kann pro Wochentag überschreiben:
- `workday_monday` ... `workday_sunday` (`null` = Modellwert verwenden)

Zusätzlich begrenzen `entry_date` und optional `exit_date` den aktiven Beschäftigungszeitraum.

## 3) Target-bearing Arbeitstage

Die tägliche Sollzeit wird nur auf **target-bearing Arbeitstage** verteilt.

Ein Tag ist target-bearing, wenn er:
1. im aktiven Beschäftigungszeitraum liegt,
2. laut aufgelöstem Arbeitsmuster ein Arbeitstag ist,
3. **kein** aktiver Feiertag ist,
4. **nicht** in einem zugewiesenen arbeitsfreien Zeitraum liegt.

Wenn eine Bedingung nicht erfüllt ist, gilt für diesen Tag `target_minutes = 0`.

## 4) Feiertage, Absenzen, arbeitsfreie Zeiträume

### Feiertag
- Wird aus HolidaySet-Logik aufgelöst (Mitarbeiter-Set vor Tenant-Default).
- Wirkung: `target_minutes = 0`, Tag ist nicht target-bearing.

### Absenz (Stage 1)
- `vacation` / `sickness`, inkl. `full_day` und halbtägigen Varianten.
- Absenz ist **Tageskontext**, nicht Capture-Status.
- Stage-1-Regel: Bei ganztägiger Absenz auf target-bearing Tagen wird für die Balance-Anzeige Sollzeit als erfüllt behandelt (Display-/MVP-Regel), `actual_minutes` bleibt eventbasiert.

### Arbeitsfreier Zeitraum (non-working period)
- Eigene Domain über `non_working_period_sets` und `non_working_periods`.
- Zuordnung über `employee.non_working_period_set_id`.
- Wirkung: `target_minutes = 0`, Tag ist nicht target-bearing.

## 5) Vorarbeitungs-Effekt

Die Jahres-Sollzeit bleibt konstant. Wenn Feiertage oder arbeitsfreie Zeiträume target-bearing Tage reduzieren, wird dieselbe Jahres-Sollzeit auf weniger Tage verteilt.

Folge:
- höhere Sollminuten auf verbleibenden target-bearing Tagen,
- keine Reduktion der vertraglichen Jahres-Sollzeit.

## 6) Zentrale Umsetzung

Die Logik ist zentral im Backend umgesetzt und wird nicht je View neu gerechnet:
- Zielzeitberechnung: `DailyAccountService`
- Periodische Aggregation: `ReportingService`
- Kalender-Mapping: `CalendarService`

Siehe auch:
- `docs/business-calendar-model.md`
- `docs/business-non-working-periods.md`
- `docs/technical-calculation-engine.md`
