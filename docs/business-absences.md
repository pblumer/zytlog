# Fachlichkeit: Absenzen (Stage 1)

Stand: 01.04.2026

## Zielbild Stage 1

Stage 1 liefert eine schlanke, produktionsnahe Absenz-Domain für:
- sichtbaren Tageskontext,
- Grundvalidierungen,
- konsistente Darstellung in Tageskonto, Reports und Kalendern.

## Unterstützte Absenztypen

- `vacation`
- `sickness`

Dauertypen:
- `full_day`
- `half_day_am`
- `half_day_pm`

## Geltende Validierungsregeln

- `end_date >= start_date`
- Mitarbeiter gehört zum Tenant
- Absenz liegt im Beschäftigungsfenster (`entry_date` / `exit_date`)
- Halbtag nur bei eintägiger Absenz
- Keine überlappenden Absenzen pro Mitarbeitendem

## Abgrenzung zu anderen Tageskontexten

### Gegenüber Feiertag
- Feiertag ist kalender-/satzbasiert (HolidaySet), nicht personenspezifisch.
- Feiertage sind keine Absenzen.

### Gegenüber arbeitsfreiem Zeitraum
- Arbeitsfreier Zeitraum ist organisatorische Regel (`non_working_period_set`), nicht individuelle Abwesenheit.
- Arbeitsfreie Zeiträume sind keine Absenzen.

## Wirkung in Tageskonto und Reporting

- Absenzen erscheinen als `absence`-Kontext in Daily Account, Week/Month/Year und Kalenderzellen.
- Capture-Status (`complete`, `incomplete`, `invalid`, `empty`) bleibt separat.

Stage-1-Vereinfachung (aktuell aktiv):
- Bei `full_day`-Absenz (`vacation`, `sickness`) auf target-bearing Tagen wird die Balance so dargestellt, als sei die Sollzeit erfüllt.
- `actual_minutes` bleibt weiterhin reine Eventsumme.

## Sichtbarkeit in der UI

- Dichte Views (Jahresraster/Kalender): kompakte Marker.
- Detailviews (Day/Week/Month): Badge + optionale AM/PM-Hinweise.

## Ausserhalb von Stage 1 (nicht implementiert)

- Genehmigungsworkflow / Manager-Freigaben
- Payroll-Integration
- Anhänge/Nachweise
- Teilstunden-Absenzen
- Komplexe Konfliktauflösung mit Zeitereignissen

Siehe auch:
- `docs/business-calendar-model.md`
- `docs/business-month-view.md`
- `docs/business-non-working-periods.md`
