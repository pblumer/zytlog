# Frontend-Views: fachlich-technischer Überblick

Stand: 01.04.2026

## Ziel

Diese Doku ordnet die zentralen Frontend-Sichten fachlich ein: welche Informationen wo sichtbar sind und wie dichte Übersicht vs. Detailansicht zusammenspielen.

## Navigationssichten

### Dashboard

Fokus:
- aktueller Clock-Status,
- heutige Kennzahlen,
- Quick-Stamp,
- kompakter Monatskalender.

Sichtbare Kontexte:
- Tagesstatus,
- heutige Absenz,
- Kalenderstatus inkl. Non-Working-Period-Hinweise.

### My Time

Fokus:
- persönlicher Schnellzugriff pro Tag,
- Kombination aus Monatskalender + Ereignisliste.

Sichtbare Kontexte:
- ausgewählter Tag mit Soll/Ist/Pause/Saldo,
- Absenzkontext,
- Statusbadge,
- schneller Sprung in Day.

### Day

Fokus:
- Detailansicht und operative Erfassung/Korrektur.

Sichtbare Inhalte:
- Tageskonto-KPIs,
- Zeitevents mit Bearbeiten/Löschen,
- manuelle Stempel,
- Tages-Timeline,
- Export für den Tag.

Kontext vs. Status:
- Tageskontext (Feiertag/Absenz/arbeitsfreier Zeitraum) wird separat vom Capture-Status geführt.

### Week

Fokus:
- tabellarische Wochenübersicht mit Tageszeilen und Wochen-Totals.

Sichtbare Kontexte:
- Tagesstatus + Tageskontexte in kompakter, aber lesbarer Form.

### Month

Fokus:
- Kalender-/Arbeitskonsole zur Mustererkennung.

Sichtbare Kontexte:
- pro Kachel: Status plus Tageskontext (Absenz, Feiertag, arbeitsfreier Zeitraum, Non-Workday),
- Summen + Kontextzähler,
- direkte Navigation zur Day-Ansicht.

### Year

Fokus:
- Jahresübersicht mit Monatskarten, Summen und Mini-Rastern.

Sichtbare Kontexte:
- Monatsstatus,
- tägliche Dot-Indikatoren,
- Absenz-Layer und Non-Working-Period-Styling in dichter Darstellung.

## Relevante Admin-Sichten

- **Employees**: Mitarbeitenden-Stammdaten inkl. Zuordnung zu Working-Time-, Holiday- und Non-Working-Period-Sets.
- **Working Time Models**: Jahresziel + Standard-Wochentagsmuster.
- **Holiday Sets / Holidays**: Feiertagsdaten inkl. OpenHolidays-Import (Preview/Commit).
- **Non-Working Period Sets**: Sets und Zeiträume für organisatorische Freiperioden.
- **Admin Absences**: tenantweite Pflege von Absenzen.

## Dichte Übersicht vs. Detailansicht

- **Dichte Sichten**: Dashboard-Kalender, Month, Year (Marker, Dots, Badges).
- **Detailsichten**: Day, teilweise Week (mehr Text, konkrete Werte, Editierbarkeit).

Die Sichten nutzen denselben Backend-Fachkern; Unterschiede liegen primär in Visualisierungsdichte und Interaktionstiefe.

## Status vs. Tageskontext (wichtig)

- **Status**: Qualität/Vollständigkeit der Zeiterfassung.
- **Tageskontext**: fachliche Einordnung (Feiertag, Absenz, arbeitsfreier Zeitraum, Non-Workday).

Beides wird bewusst getrennt dargestellt, um Fehlinterpretationen zu vermeiden.

Siehe auch:
- `docs/business-calendar-model.md`
- `docs/business-month-view.md`
- `frontend/README.md`
