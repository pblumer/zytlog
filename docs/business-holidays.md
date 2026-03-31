# Fachlichkeit: Feiertage als tenant-spezifischer Zielzeitfaktor

Dieses Dokument beschreibt die Feiertagssemantik in Zytlog (Stand: 31.03.2026).

## 1) Was ist ein Feiertag in Zytlog?

Ein Feiertag ist ein **tenant-spezifischer Kalendereintrag** mit Datum und Name.

- Feiertage sind keine Zeitstempel.
- Feiertage sind keine Abwesenheiten.
- Feiertage gehören nicht einer einzelnen Person, sondern einem Tenant.

## 2) Tenant-Scope

Jeder Tenant verwaltet seinen eigenen Feiertagskalender.

- Gleiche Daten können in unterschiedlichen Tenants existieren.
- Pro Tenant ist ein Datum eindeutig (`tenant_id + date`).

## 3) Wirkung auf Zielzeit

Feiertage wirken nur auf die **Soll-Seite**:

- Wenn ein Datum ein aktiver Feiertag ist, gilt: `target_minutes = 0`.
- Der Tag zählt nicht als target-bearing workday.
- Das gilt auch dann, wenn der Wochentag laut Arbeitsmuster normalerweise ein Arbeitstag wäre.

## 4) Verteilung der Jahresarbeitszeit

Die Jahresarbeitszeit (`annual_target_hours`) bleibt unverändert.

Feiertage reduzieren die Anzahl target-bearing Arbeitstage im Jahr. Dadurch steigt die Tageszielzeit auf den verbleibenden target-bearing Tagen.

### Beispiel

- `annual_target_hours = 2080`
- Mitarbeitende arbeiten Mo–Fr
- Relevante Arbeitstage ohne Feiertage: `260`
- Feiertage auf target-bearing Werktagen: `10`
- Neue target-bearing Arbeitstage: `250`
- Tagesziel: `2080 / 250 = 8.32h`

Das ist beabsichtigt: Die Jahres-Sollzeit bleibt konstant, nur die Verteilung ändert sich.

## 5) Abgrenzung zu zukünftigen Abwesenheiten

Feiertage sind ein eigener Fachbegriff und werden nicht als Absenzobjekt modelliert.

Zukünftige Konzepte (noch nicht implementiert):

- Ferien/Urlaub
- Krankheit
- Halbtage
- Genehmigungsworkflows

Erwartete Richtung:
- Feiertage bleiben global pro Tenant.
- Ferien/Krankheit werden später personengebundene Abwesenheiten mit eigenen Regeln.
