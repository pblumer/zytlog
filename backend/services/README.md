Service layer orchestrates tenant-scoped use-cases and validations.

Examples for next steps:
- `clocking_service.py`
- `reporting_service.py`
- `working_time_model_service.py`


## Time tracking
- `TimeTrackingService` enforces alternating `CLOCK_IN`/`CLOCK_OUT` events per employee and tenant.
- `DailyAccountService` computes daily target/actual/break/balance values from same-day clock events.
- Daily break minutes are currently inferred as gaps between completed work intervals (MVP simplification).

- `ReportingService` builds week/month/year overview payloads from daily account calculations.
