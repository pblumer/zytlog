# Business View: Month-Konsole

Stand: 01.04.2026

## Zweck

Die Month-Seite ist eine **Kalender- und Arbeitskonsole**:
- Tagesmuster im Monatskontext schnell erkennen,
- problematische Erfassungen identifizieren,
- direkt in die Day-Ansicht springen.

Sie ist bewusst mehr als eine reine Summenliste.

## Datenquelle

Month basiert auf dem Monatsreport:
- `GET /api/v1/reports/my/month?year=YYYY&month=MM`

Die Kacheln nutzen Tagesdaten aus demselben berechneten Tageskonto wie Day/Week/Year.

## Pro Tag sichtbare Informationen

Jede Kachel kann enthalten:
- Datum
- `target_minutes`
- `actual_minutes`
- `balance_minutes`
- Capture-Status (`complete`, `incomplete`, `invalid`, `empty`)
- Tageskontext (Absenz, Feiertag, arbeitsfreier Zeitraum, Non-Workday)
- optional Feiertagsname bzw. Bezeichnung des arbeitsfreien Zeitraums

`empty` wird als fehlende Erfassungsdaten („No data“) dargestellt, nicht als gearbeitetes `00:00`.

## Trennung: Status vs Kontext

Die Month-Konsole trennt zwei Achsen strikt:

1. **Capture-Status** (Datenqualität)
   - `complete`, `incomplete`, `invalid`, `empty`

2. **Tageskontext** (fachliche Kalendereinordnung)
   - `absence`
   - `non_working_period`
   - `holiday`
   - `workday` / `non_workday`

Diese Trennung verhindert semantische Überladung einzelner Marker.

## Non-working periods in Month

Arbeitsfreie Zeiträume sind explizit Teil der Month-Darstellung:
- eigener Kontextmarker / Badge,
- eigener Zähler in der Monatszusammenfassung,
- `target_minutes = 0` an betroffenen Tagen.

Sie bleiben klar von Feiertagen und Absenzen getrennt.

## Interaction Model

- Klick auf Tageskachel öffnet `/day?date=YYYY-MM-DD`.
- Damit dient Month als schnelle Navigations- und Prüfoberfläche.

Siehe auch:
- `docs/business-calendar-model.md`
- `docs/business-working-time-model.md`
- `docs/frontend-views.md`
