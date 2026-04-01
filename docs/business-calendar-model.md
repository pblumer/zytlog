# Fachlichkeit: Kalenderkontext und Tagesstatus

Stand: 01.04.2026

## Ziel

Dieses Dokument trennt die drei Ebenen der Tagesdarstellung in Zytlog klar:
1. **Metriken** (Soll/Ist/Pause/Saldo)
2. **Capture-Status** (Datenqualität der Zeiterfassung)
3. **Tageskontext** (fachliche Kalendereinordnung)

## 1) Metriken

Pro Tag werden mindestens folgende Metriken geführt:
- `target_minutes`
- `actual_minutes`
- `break_minutes`
- `balance_minutes`
- `event_count`

Diese Werte stammen aus der zentralen Tageskonto-Berechnung.

## 2) Capture-Status (separat von Kontext)

Capture-Status beschreibt nur die Qualität/Vollständigkeit der Ereignisse:
- `complete`
- `incomplete`
- `invalid`
- `empty`

Im Kalender-API wird `empty` als `no_data` abgebildet.

Wichtig: Capture-Status sagt **nicht**, ob ein Tag Feiertag/Absenz/arbeitsfreier Zeitraum ist.

## 3) Tageskontext

Der Tageskontext beschreibt die fachliche Einordnung des Datums.

### Feiertag
- Kontextfelder: `is_holiday`, `holiday_name`
- Wirkung: `target_minutes = 0`, nicht target-bearing.

### Absenz
- Kontextfeld: `absence` (Typ + Label + Dauer)
- Wirkung: Sichtbarkeit des Personenkontexts, getrennt vom Capture-Status.
- Stage-1-Regel für Balance bei ganztägiger Absenz bleibt aktiv.

### Arbeitsfreier Zeitraum
- Kontextfelder: `is_in_non_working_period`, `non_working_period_label`
- Wirkung: `target_minutes = 0`, nicht target-bearing.

## 4) Priorisierte Kontextauswertung in der UI

Für dichte Kalenderdarstellungen wird typischerweise folgende Priorität verwendet:
1. `absence`
2. `is_in_non_working_period`
3. `is_holiday`
4. `is_workday` / non-workday

So bleiben Konflikte bei Badge-/Farbwahl beherrschbar, ohne Capture-Status zu überladen.

## 5) API- und UI-Sicht

- Tages- und Report-DTOs enthalten Metriken + Status + Kontextfelder parallel.
- Month/Year zeigen dichte visuelle Marker.
- Day/Week zeigen mehr Detailtiefe (z. B. konkrete Absenz-Dauer AM/PM).

Siehe auch:
- `docs/business-working-time-model.md`
- `docs/business-month-view.md`
- `docs/frontend-views.md`
