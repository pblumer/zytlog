# Business Rules: Absences (Stage 1)

## Scope
Stage 1 introduces a slim absence domain for **visibility and basic data integrity**.

Supported absence types:
- `vacation`
- `sickness`

Supported duration types:
- `full_day`
- `half_day_am`
- `half_day_pm`

## What Stage 1 does
- Persists tenant-scoped absences per employee and date range.
- Validates:
  - `end_date >= start_date`
  - employee belongs to tenant
  - absence lies in entry/exit employment range
  - half-day only for single-day absences
  - no overlapping absences for the same employee
- Exposes absences in:
  - daily account API (`absence` context)
  - weekly/monthly/yearly reports (via daily rows)
  - calendar month API (`absence` per day cell)
  - overview UI rendering: Dashboard, My Time, Day, Week, Month, Year

## Separation of concerns
- **Capture status** (`complete`, `incomplete`, `invalid`, `empty`) remains independent.
- **Day context** can include holiday and absence information.
- **Holidays and absences stay separate concepts**:
  - Holiday is calendar/tenant policy context.
  - Absence is employee-specific context.
- Different overview screens can show absence with different detail density:
  - compact marker in dense views (calendar/year dots),
  - badge with AM/PM hint in detailed views (day/week/month).

## Stage-1 simplification for balance display
- For full-day vacation/sickness on target-bearing days, daily balance is treated as target-fulfilled.
- `actual_minutes` remains based on recorded events.
- This is a temporary display/business simplification for MVP usability.

## Out of scope (Stage 2+)
- Approval workflow
- Manager review
- Payroll export integration
- Attachments/certificates
- Partial-hour absences
- Complex reconciliation with conflicting time events
