# Technische Übersicht: Calculation Engine

Stand: 01.04.2026

## Ziel

Diese Übersicht beschreibt die zentrale Berechnungslogik für Tageskonto, Kalender und Reporting im Backend.

Prinzip: Fachlogik wird **einmal** zentral berechnet und in mehreren Views/Reports wiederverwendet.

## Architekturbausteine

### DailyAccountService

Verantwortung:
- Berechnet Tageskonto pro Datum (`target_minutes`, `actual_minutes`, `break_minutes`, `balance_minutes`, Status, Kontextfelder).
- Löst Jahreskontext auf (Arbeitsmuster, Feiertage, arbeitsfreie Zeiträume, relevante Arbeitstage).
- Wendet annual-target-Logik auf Tagesebene an.

Wichtige Aspekte:
- `annual_target_hours` + `employment_percentage` bilden die jährliche Sollminutenbasis.
- `target_minutes = 0` bei Nicht-Arbeitstag, Feiertag, arbeitsfreiem Zeitraum, außerhalb von Entry/Exit.
- Absenzkontext wird ergänzt; Stage-1-Balance-Regel für ganztägige Absenzen ist integriert.

### ReportingService

Verantwortung:
- Baut Week/Month/Year-Overviews auf Basis von DailyAccountService.
- Aggregiert Tageswerte zu Totals (inkl. Statuszähler).
- Berechnet Monatssummen im Jahresreport.

Wichtig:
- Keine parallele Fachlogik – Reporting konsumiert Tageskonto-Ergebnisse.

### CalendarService

Verantwortung:
- Leitet Monatssichten aus Monatsreport ab.
- Mappt Tagesstatus für Kalenderdarstellung (`empty` -> `no_data`).
- Reicht Kontextinformationen (Absenz, non-working period) in kalendergeeigneter Form durch.

## Zusammenhang Tageskonto ↔ Reports

Datenfluss (vereinfacht):
1. `DailyAccountService` erzeugt konsistente Tagesdatensätze.
2. `ReportingService` aggregiert diese Datensätze für Woche/Monat/Jahr.
3. `CalendarService` nutzt Monatsdaten für kalenderorientierte UI.

Damit stimmen Zahlen und Kontexte zwischen Day/Week/Month/Year konsistent überein.

## Jahreskontext und Performance

Für Bereiche über viele Tage (Month/Year) wird der Jahreskontext vorab berechnet und wiederverwendet:
- Auflösung Arbeitsmuster pro Jahr,
- Laden von Feiertagen im Jahresfenster,
- Laden/Expandieren arbeitsfreier Zeiträume,
- Zählung relevanter target-bearing Arbeitstage.

Der Kontext wird pro Jahr gecacht und über Tagesschleifen wiederverwendet. Das reduziert wiederholte Berechnungen und unterstützt schnelle Month/Year-Antworten.

## Ergebnis

Die zentrale Calculation Engine im Backend stellt sicher:
- einheitliche Fachlogik,
- konsistente KPI-/Statuswerte in allen Sichten,
- gute Erweiterbarkeit (z. B. weitere Kontextarten) ohne Logikduplikate.

Siehe auch:
- `backend/services/daily_account_service.py`
- `backend/services/reporting_service.py`
- `backend/services/calendar_service.py`
- `docs/business-working-time-model.md`
