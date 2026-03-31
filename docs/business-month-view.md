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
- absence context marker (`absence`, e.g. vacation/sickness with optional AM/PM)

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
   - `absence` (vacation, sickness)

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

## Absence context contract

Month uses the same day-context contract as other overview screens:

- `absence: { type: string, label: string, duration_type: string } | null`

Absence stays a context layer (not status) and is rendered as badge-level context.

Important boundary:

- Holidays remain their own context (holiday-set driven) and are **not** absences.


## Absence context in Month view

- Month tiles can display an absence badge (`Vacation`, `Sickness`).
- Half-day absences are shown with restrained AM/PM hint.
- Holidays remain independently visible and are not mapped to absence.
- Capture quality status dots remain unchanged and separate from context badges.
