# Fachlichkeit: Jahresarbeitszeit als führende Sollgrösse

Dieses Dokument beschreibt die verbindliche Zielzeit-Logik für Zytlog (Stand: 31.03.2026).

## 1) Fachliche Korrektur: Eine einzige führende Sollgrösse

Das Modell mit gleichzeitig pflegbaren `weekly_target_hours` und `annual_target_hours` wurde entfernt.

**Neue Regel:**
- `annual_target_hours` ist die **führende Sollgrösse** des `WorkingTimeModel`.
- Wochenzielstunden werden nicht mehr gespeichert und nicht mehr in der UI gepflegt.

Begründung:
- Zwei unabhängige Zielgrössen erzeugen Widersprüche.
- Die Jahresarbeitszeit ist die stabilere Basis für spätere Feiertag-/Abwesenheitslogik.

## 2) WorkingTimeModel (Standardmuster)

Ein `WorkingTimeModel` enthält:
- `name`
- `annual_target_hours` (verpflichtend)
- `default_workday_monday` ... `default_workday_sunday`
- `active`

Die Anzahl Standard-Arbeitstage pro Woche wird **nicht separat gespeichert**, sondern bei Bedarf aus den Wochentag-Flags abgeleitet.

## 3) Employee (individuelle Zuordnung)

Ein `Employee` erweitert das Modell mit:
- `employment_percentage` (Arbeitspensum)
- `working_time_model_id`
- `entry_date` / `exit_date`
- optionalen Overrides `workday_monday` ... `workday_sunday`

Override-Regel:
- Employee-Override gesetzt (`true`/`false`) -> überschreibt Modellwert.
- Override `null` -> Standard-Arbeitstag aus Modell gilt.

## 4) Autoritative Berechnung der Tageszielzeit

Die Tageszielzeit wird zentral im Backend berechnet und von Tagesansicht, Kalender sowie Woche/Monat/Jahr-Reports identisch verwendet.

### Schrittfolge

1. **Aktive Arbeitstage für Mitarbeitende bestimmen**
   - Wochentag-Override des Mitarbeitenden, sonst Modellstandard.

2. **Relevante Arbeitstage des Kalenderjahres bestimmen**
   - Nur Tage innerhalb `entry_date`/`exit_date`.
   - Nur Tage, deren Wochentag aktiv ist.
   - Noch ohne Feiertags-/Ferien-/Krankheitsabzug.

3. **Effektive Jahreszielzeit berechnen**
   - `effective_annual_target_hours = annual_target_hours * employment_percentage / 100`

4. **Gleichmässig über relevante Arbeitstage verteilen**
   - `daily_target_hours = effective_annual_target_hours / number_of_relevant_workdays_in_year`
   - Umrechnung in Minuten, Rundung auf ganze Minuten.

## 5) Nicht-Arbeitstage

Für Tage ohne reguläre Arbeitspflicht gilt `target_minutes = 0`:
- Wochentag inaktiv,
- vor `entry_date`,
- nach `exit_date`.

## 6) Zukunftssemantik (noch nicht implementiert)

### Feiertage
- Feiertage sind später **keine target-bearing workdays**.
- Sie reduzieren also die Anzahl relevanter Jahres-Arbeitstage.

### Ferien/Urlaub
- Ferien reduzieren **nicht** die Jahresarbeitszeit.
- Der Tag bleibt target-bearing workday; Zielzeit gilt fachlich als durch Abwesenheit erfüllt.

### Krankheit
- Gleiche Richtung wie Ferien (vorläufig): kein „verlorener Solltag“ per Default.
- Exakte HR-Details können später verfeinert werden.

## 7) Beispiele

### Beispiel A: 100%
- Modell: `annual_target_hours = 2080`
- Aktive Arbeitstage: Mo–Fr
- Mitarbeitender: 100%
- Relevante Arbeitstage im Jahr: z. B. 260 (ohne spätere Feiertagslogik)
- Tagesziel: `2080 / 260 = 8h` -> `480` Minuten

### Beispiel B: 80% mit Override
- Modell: `annual_target_hours = 2080`
- Mitarbeitender: 80%
- Override-Arbeitstage: Mo, Di, Do, Fr
- Effektive Jahreszielzeit: `1664h`
- Relevante Arbeitstage: Anzahl Mo/Di/Do/Fr im aktiven Beschäftigungszeitraum
- Tagesziel: `1664 / relevante_arbeitstage`

## 8) Warum diese Richtung fachlich korrekt ist

Diese Korrektur schafft eine klare, erweiterbare Basis:
- exakt **eine** führende Sollgrösse,
- saubere Pensum-Logik auf Jahressicht,
- konsistente Tagesziele für alle Auswertungen,
- vorbereitet für Feiertag/Ferien/Krankheit ohne Modellbruch.
