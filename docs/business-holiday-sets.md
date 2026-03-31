# Fachlichkeit: Feiertagssätze (Feiertagssatz-basierte Zielzeit)

Dieses Dokument beschreibt die Feiertags-Fachlichkeit nach der Umstellung von tenant-weiten Feiertagen auf **Feiertagssätze**.

## Warum wurde das alte Modell ersetzt?

Früher gab es pro Tenant nur einen gemeinsamen Feiertagskalender. Das ist in der Praxis zu unflexibel, weil ein Tenant Mitarbeitende in unterschiedlichen Kantonen/Regionen haben kann.

Mit Feiertagssätzen kann ein Tenant mehrere wiederverwendbare Feiertagskalender pflegen, z. B.:
- `BE Standard`
- `ZH Standard`
- `ZH mit lokalen Ergänzungen`

## Kernmodell

- `HolidaySet`: Gruppiert zusammengehörige Feiertage.
- `Holiday`: Gehört genau zu einem `HolidaySet`.
- `Employee.holiday_set_id` (optional): Mitarbeiter-spezifische Zuordnung.
- `Tenant.default_holiday_set_id` (optional): Tenant-Standard für alle ohne explizite Mitarbeiter-Zuordnung.

Regel für die effektive Zuordnung:
1. Wenn `employee.holiday_set_id` gesetzt ist, gilt dieser Feiertagssatz.
2. Sonst gilt `tenant.default_holiday_set_id` (falls vorhanden).
3. Sonst gibt es keine Feiertagswirkung für diesen Mitarbeitenden.

## Wirkung auf die Zielzeitberechnung

Die Zielzeitlogik bleibt zentral im Tageskonto-Service und arbeitet in dieser Reihenfolge:

1. Ist das Datum laut Arbeitsmuster ein normaler Arbeitstag?
2. Effektiven Feiertagssatz auflösen (Mitarbeiter-Override vor Tenant-Default).
3. Prüfen, ob das Datum als aktiver Feiertag im effektiven Satz existiert.
4. Falls ja: `target_minutes = 0`.
5. Falls nein: normale annual-target-basierte Verteilung anwenden.

## Warum bleibt `annual_target_hours` konstant?

Die Jahres-Sollzeit ist die führende Vertragsgröße. Feiertage reduzieren daher nicht die Jahres-Sollzeit, sondern die Anzahl target-bearing Arbeitstage.

Folge: Die verbleibenden target-bearing Tage tragen anteilig mehr Sollminuten.

## Beispiele

### Beispiel A
- Tenant hat zwei Feiertagssätze: `BE Standard`, `ZH Standard`.
- Tenant-Standard = `BE Standard`.
- Die meisten Mitarbeitenden nutzen damit automatisch Berner Feiertage.

### Beispiel B
- Ein Mitarbeitender wird auf `ZH Standard` gesetzt.
- An einem nur in Zürich gültigen Feiertag gilt:
  - Für diesen Mitarbeitenden `target_minutes = 0`.
  - Mitarbeitende mit `BE Standard` haben normale Zielzeit, sofern es in BE kein Feiertag ist.

### Beispiel C
- Tenant pflegt `ZH mit lokalen Ergänzungen`.
- Damit können importierte kantonale Standards plus tenant-spezifische Zusatzfeiertage kombiniert werden.

## Ergebnis

Das Modell passt deutlich besser zu realen Schweizer Standort-/Kanton-Szenarien, bleibt tenant-sicher und ist kompatibel mit zukünftigen Importquellen (z. B. kantonale Datensätze).

## OpenHolidays als Importquelle

Für Admins steht ein manueller Import-Workflow mit Vorschau/Commit zur Verfügung, der OpenHolidays-Daten in einen ausgewählten Feiertagssatz übernimmt.

- Importquelle: OpenHolidays (Land, Sprache, optionale Subdivision, Zeitraum).
- Ziel: bestehender Feiertagssatz im Tenant.
- Konfliktstrategie: `skip_existing` oder `replace_existing_in_range` (Matching primär über Datum innerhalb des Feiertagssatzes).

Wichtig: Die Laufzeitlogik für Zielzeitberechnung bleibt unverändert und nutzt weiterhin nur Zytlog-interne Feiertagsdaten.
