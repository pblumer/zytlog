# Fachlichkeit: Feiertage

Die Feiertags-Fachlichkeit in Zytlog basiert auf **Feiertagssätzen**. Feiertage werden in der eigenen Zytlog-Datenbank gespeichert und dort gepflegt (manuell oder per Import).

## OpenHolidays-Import (admin, manuell)

Zytlog unterstützt im Admin-Bereich einen manuellen Import aus OpenHolidays in einen **konkret ausgewählten Feiertagssatz**.

Wichtige Produktentscheidung:
- OpenHolidays ist **nur eine Importquelle**.
- Die tägliche Zielzeitberechnung nutzt weiterhin ausschließlich die in Zytlog gespeicherten Feiertage.
- Es gibt keine Laufzeit-Abhängigkeit von OpenHolidays für Tageskonten oder Reporting.

## Workflow (Preview + Commit)

1. Feiertagssatz auswählen
2. Land (`country_iso_code`) wählen
3. Optional Subdivision/Region (`subdivision_code`) wählen
4. Sprache (`language_code`) wählen
5. Zeitraum (`valid_from`, `valid_to`) wählen
6. Vorschau laden
7. Vorschau prüfen
8. Import bestätigen

Die Vorschau zeigt pro Datensatz:
- Datum
- Feiertagsname
- Herkunft (`source=openholidays`)
- Ob im gewählten Feiertagssatz bereits ein Feiertag am Datum existiert
- Aktion (`create`, `skip`, `replace`)

## Duplicate-/Konfliktstrategie

Abgleichsbasis ist **Feiertagssatz + Datum**.

Unterstützte Modi:
- `skip_existing`: vorhandene Feiertage im Satz bleiben unverändert, neue werden ergänzt.
- `replace_existing_in_range`: vorhandene Feiertage auf gleichen Daten im Importbereich werden ersetzt.

## Tenant- und Rollenregeln

- Import ist admin-only.
- Alle Endpunkte sind tenant-scoped.
- Importziel ist immer genau ein Feiertagssatz innerhalb des aktuellen Tenants.
- Kein tenant-weites Blind-Importieren.

## Abgrenzung zu Absenzen

Importierte Feiertage bleiben Feiertage und werden **nicht** als Absenzen gespeichert oder interpretiert.

## Verwandte Dokumentation

- `docs/business-holiday-sets.md`
