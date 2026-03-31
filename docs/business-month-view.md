# Business View: Month Console

## Purpose

The Month page is a working console for daily control in a monthly context.
It is not a pure report table. Users should be able to scan each day quickly, detect issues, and jump into the Day page for corrections.

## Data Source and Scope

The page reuses the existing monthly reporting endpoint:

- `GET /api/v1/reports/my/month?year=YYYY&month=MM`

No dedicated month-calendar endpoint is required for this use case.

## Per-day Information in Calendar Tiles

Each day tile can display:

- day number
- target minutes
- actual minutes (primary visual value)
- balance minutes
- capture status (`complete`, `incomplete`, `invalid`, `empty`)
- holiday marker and holiday name (if applicable)
- workday/non-workday marker (`is_workday`)

Presentation notes:

- `empty` capture status is shown as missing capture data ("No data"), not as a recorded `00:00` work result.
- On days with `target_minutes = 0`, balance remains calculated but is visually de-emphasized.
- Default workdays are treated as implicit context and do not require a visible "Workday" badge on every tile.

Each tile links to:

- `/day?date=YYYY-MM-DD`

## Domain Distinction: Day Context vs Capture Status

The Month view keeps two conceptual dimensions separate:

1. **Day context** (calendar semantics)
   - `workday`
   - `non-workday`
   - `holiday`
   - reserved future context: absence markers (vacation, sickness)

2. **Time capture status** (data quality/completeness semantics)
   - `complete`
   - `incomplete`
   - `invalid`
   - `empty`

This separation avoids overloading one field with conflicting meanings.

## Holiday Handling

Holidays are represented by existing holiday-set logic and shown as explicit holiday context in month tiles.

- Holidays are not absences.
- Holidays produce `target_minutes = 0`.
- Holidays reduce target-bearing workdays in annual target distribution.

## Forward Compatibility for Absence Integration

Absences are not implemented in the MVP yet, but the Month page layout intentionally reserves a dedicated day-context channel.

Future absence integration should:

- extend day-context markers (not capture status)
- keep capture status semantics unchanged
- avoid requiring a Month page redesign
