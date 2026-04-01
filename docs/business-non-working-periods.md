# Fachlichkeit: Arbeitsfreie Zeiträume (non-working periods)

Stand: 01.04.2026

## Definition

Arbeitsfreie Zeiträume sind organisatorische Zeitfenster, in denen für eine definierte Mitarbeitendengruppe keine reguläre Sollarbeitszeit anfällt.

In Zytlog sind sie als eigene Domain modelliert:
- `non_working_period_sets`
- `non_working_periods`
- optionale Zuordnung pro Mitarbeiter: `employee.non_working_period_set_id`

## Motivation

Das Konzept deckt Fälle ab, die weder klassischer Feiertag noch individuelle Absenz sind, z. B.:
- Schulferien für schulnahe Teams,
- Betriebsruhe,
- organisationsspezifische Freiperioden.

## Abgrenzung

### Gegenüber Feiertag
- Feiertag: kalender-/gesetzesbezogen, typischerweise standortabhängig.
- Arbeitsfreier Zeitraum: organisationsbezogene Regel im Tenant.

### Gegenüber Absenz
- Absenz: personenspezifische Verhinderung (`vacation`, `sickness`).
- Arbeitsfreier Zeitraum: gruppen-/regelbasierte Nicht-Arbeitszeit, keine individuelle Abwesenheit.

## Set- und Zuordnungslogik

1. Admins verwalten `non_working_period_sets`.
2. Ein Set enthält mehrere `non_working_periods` mit `start_date`, `end_date`, `name`, optional `category`.
3. Ein Mitarbeiter kann optional einem Set zugeordnet werden.
4. Ohne Zuordnung wirkt kein arbeitsfreier Zeitraum für den Mitarbeiter.

## Wirkung auf Zielzeit und target-bearing workdays

Wenn ein Tag innerhalb eines zugewiesenen arbeitsfreien Zeitraums liegt:
- `target_minutes = 0`
- der Tag zählt **nicht** als target-bearing Arbeitstag

Die jährliche Sollzeit (`annual_target_hours`) bleibt unverändert.

## Vorarbeitungs-Effekt

Da die Jahres-Sollzeit konstant bleibt, wird sie auf weniger target-bearing Tage verteilt, wenn arbeitsfreie Zeiträume vorhanden sind.

Konsequenz:
- höhere Sollminuten an verbleibenden target-bearing Tagen,
- keine automatische Reduktion der Jahres-Sollstunden.

## Sichtbarkeit in API und UI

Tagesbezogene Antworten tragen explizite Kontextfelder:
- `is_in_non_working_period`
- `non_working_period_label`

Month/Year zeigen diesen Kontext als eigene visuelle Ebene.

Siehe auch:
- `docs/business-working-time-model.md`
- `docs/business-calendar-model.md`
- `docs/business-month-view.md`
