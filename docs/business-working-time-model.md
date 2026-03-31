# Fachlichkeit: Arbeitszeitmodell, Pensum und Tageszielzeit

Dieses Dokument beschreibt die **verbindliche MVP-Berechnungslogik** für Zytlog (Stand: 31.03.2026).

## 1) WorkingTimeModel (Standardmuster)

Ein `WorkingTimeModel` beschreibt die Standard-Arbeitslogik eines Teams/einer Firma:

- `weekly_target_hours` = Wochenzielstunden bei **100% Arbeitspensum**
- `annual_target_hours` (optional) = Jahresarbeitszeit für spätere Reports
- `default_workday_monday` ... `default_workday_sunday` = Standard-Arbeitstage
- `default_workdays_per_week` = Anzahl Standard-Arbeitstage (aus UI-Sicht informativ)
- `active` = Modell ist aktiv/inaktiv

## 2) Employee (individuelle Zuordnung)

Ein `Employee` erweitert das Modell um persönliche Parameter:

- `employment_percentage` = Arbeitspensum (z. B. 80)
- `working_time_model_id` = verknüpftes Standardmodell
- `entry_date` / `exit_date` = aktiver Beschäftigungszeitraum
- optionale Overrides `workday_monday` ... `workday_sunday`

### Override-Regel

- Wenn `workday_<weekday>` beim Employee **gesetzt** ist (`true`/`false`), überschreibt dieser Wert den Modell-Standard.
- Wenn `workday_<weekday>` beim Employee **null** ist, gilt der entsprechende `default_workday_<weekday>` aus dem Modell.

Damit sind Muster wie „80% mit Mittwoch frei“ sauber abbildbar.

## 3) Autoritative Tagesziel-Berechnung

Die Tageszielzeit wird zentral in der Backend-Service-Logik berechnet und von Tagesansicht, Kalender und Reports gemeinsam genutzt.

### Schrittfolge

1. **Aktive Beschäftigung prüfen**
   - vor `entry_date` => `target_minutes = 0`
   - nach `exit_date` (falls gesetzt) => `target_minutes = 0`
2. **Effektives Wochenziel berechnen**
   - `effective_weekly_target_hours = weekly_target_hours * employment_percentage / 100`
3. **Aktive Arbeitstage ermitteln**
   - Employee-Override falls gesetzt, sonst Modell-Standard
4. **Ist der Kalendertag kein aktiver Arbeitstag?**
   - `target_minutes = 0`
5. **Wenn aktiver Arbeitstag:**
   - gleichmäßige Verteilung auf alle aktiven Arbeitstage
   - `daily_target_hours = effective_weekly_target_hours / number_of_active_workdays`
   - Umrechnung in Minuten (gerundet auf ganze Minuten)

## 4) Verhalten für Nicht-Arbeitstage

Für reguläre Nicht-Arbeitstage (z. B. Samstag/Sonntag bei Mo-Fr-Modell oder ein individuell freier Mittwoch) gilt:

- `target_minutes = 0`
- Der Tag ist im Sinne der Zielzeit kein regulärer Arbeitstag.

## 5) Bedeutung von annual_target_hours (MVP)

`annual_target_hours` ist in diesem Schritt **optional** und dient derzeit primär für Transparenz/kommende Auswertungen.

Wichtig:
- Die tägliche Sollzeit basiert in diesem Schritt ausschließlich auf `weekly_target_hours` + Pensum + Arbeitstage.
- Es gibt **noch keine** Jahresausgleichslogik.

## 6) Beispiele

### Beispiel A

- Modell: 42h/Woche, Arbeitstage Mo-Fr
- Mitarbeiter: 100%
- Ergebnis:
  - Effektives Wochenziel = 42h
  - Aktive Arbeitstage = 5
  - Tagesziel = 8.4h = 504 Minuten auf Mo-Fr
  - Sa/So = 0 Minuten

### Beispiel B

- Modell: 42h/Woche, Arbeitstage Mo-Fr
- Mitarbeiter: 80%
- Employee-Override: Mo, Di, Do, Fr aktiv; Mi inaktiv
- Ergebnis:
  - Effektives Wochenziel = 33.6h
  - Aktive Arbeitstage = 4
  - Tagesziel = 8.4h = 504 Minuten auf Mo/Di/Do/Fr
  - Mi/Sa/So = 0 Minuten

## 7) Bewusst noch nicht implementiert

Nicht Teil dieses Schritts:

- Ferien/Urlaub
- Krankheit
- Feiertagskalender
- halbe Ausfalltage
- variable Verteilung der Tageszielstunden pro Wochentag
- zusätzliche Überstundenregeln/Approval-Flows

Die aktuelle Struktur ist bewusst so umgesetzt, dass diese Themen später auf die bestehende Zielzeitlogik aufbauen können.
