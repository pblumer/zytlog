# Zytlog UI-Optimierung: Umsetzungsplan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Zytlogs UI konsistent, barrierefrei und wartbar machen -- Sprachmix bereinigen, Design-System-Grundlagen schaffen, hartcodierte Werte eliminieren, Barrierefreiheit verbessern.

**Architecture:** Schrittweise Refaktorisierung ohne Breaking Changes. Jede Phase ist eigenständig deploybar. CSS wird pro Komponente aufgeteilt, Design-Tokens zentralisiert, i18n wird als Konstanten-Map eingeführt (kein Framework-Overkill).

**Tech Stack:** React 19, TypeScript, Vite, reines CSS (kein CSS-in-JS), TanStack Query

---

## Phase 1: Design-Tokens und CSS-Grundlagen

### Task 1.1: Neue CSS-Variablen in styles.css einführen

**Objective:** Spacing-, Typografie- und Farb-Tokens als CSS Custom Properties definieren.

**Files:**
- Modify: `frontend/src/theme/styles.css`

**Step 1: Spacing-Tokens ergänzen**

Füge nach den bestehenden `:root`-Variablen ein Spacing-Scale hinzu:

```css
:root {
  /* bestehende Variablen bleiben */

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;

  /* Typografie */
  --text-xs: 0.7rem;
  --text-sm: 0.8rem;
  --text-base: 0.92rem;
  --text-md: 1rem;
  --text-lg: 1.1rem;
  --text-xl: 1.25rem;

  /* Semantische Farben */
  --color-balance-positive: #2e7d32;
  --color-balance-negative: #b3261e;
  --color-status-success-bg: #eaf7e0;
  --color-status-success-text: #2e7d32;
  --color-status-info-bg: #e8f0fe;
  --color-status-info-text: #1a73e8;
  --color-status-warning-bg: #fff5dd;
  --color-status-warning-text: #b8860b;
  --color-status-danger-bg: #fdecef;
  --color-status-danger-text: #a73645;
  --color-danger-hover: #8f2d3b;
  --color-editing-row: #eef3fb;
  --color-overlay: rgba(13, 22, 35, 0.42);

  /* Kalender-Statusfarben */
  --color-cal-complete: #a3be8c;
  --color-cal-complete-bg: #eaf7e0;
  --color-cal-incomplete: #d08770;
  --color-cal-incomplete-bg: #fde8d8;
  --color-cal-invalid: #bf616a;
  --color-cal-invalid-bg: #fdecef;
  --color-cal-empty: #d8dee9;
  --color-cal-holiday: #81a1c1;
  --color-cal-holiday-bg: #e8f0fe;
  --color-cal-absence: #b48ead;
  --color-cal-absence-bg: #f4e8f4;
  --color-cal-nonwork: #ebcb8b;
  --color-cal-nonwork-bg: #fff5dd;

  /* Border-Radius */
  --radius-sm: 6px;
  --radius-md: var(--radius); /* 10px */
  --radius-lg: 14px;
  --radius-full: 999px;
}
```

**Step 2: Commit**

```bash
git add frontend/src/theme/styles.css
git commit -m "feat(ui): add spacing, typography and semantic color tokens"
```

---

### Task 1.2: tokens.ts entfernen (Totcode)

**Objective:** Ungenutzte Nord-Token-Referenz entfernen.

**Files:**
- Delete: `frontend/src/theme/tokens.ts`

**Step 1: Datei löschen**

```bash
rm frontend/src/theme/tokens.ts
```

**Step 2: Prüfen, dass kein Import existiert**

```bash
grep -r "tokens" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v node_modules
```

Erwartet: Keine Importe von `tokens.ts`.

**Step 3: Commit**

```bash
git add -A
git commit -m "chore(ui): remove unused tokens.ts"
```

---

### Task 1.3: Hartcodierte Farben in ui.css durch Variablen ersetzen

**Objective:** Alle hartcodierten Hex-Werte in `ui.css` durch die neuen CSS-Variablen ersetzen.

**Files:**
- Modify: `frontend/src/components/ui.css`

**Step 1: Button-Farben**

Ersetze:
- `.btn.danger` Hintergrund `#a73645` → `var(--danger)` (bereits `#bf616a`, nahe genug; oder `var(--color-status-danger-text)` für den dunkleren Ton)
- `.btn.danger:hover` `#8f2d3b` → `var(--color-danger-hover)`
- `.btn.danger:active` → `var(--color-danger-hover)`

**Step 2: Status-Farben**

Ersetze in `.status.success`, `.status.info`, `.status.warning`, `.status.danger`:
- Background- und Text-Farben durch `var(--color-status-*-bg)` und `var(--color-status-*-text)`

**Step 3: Balance-Farben**

Ersetze:
- `.balance-positive` Farbe `#2e7d32` → `var(--color-balance-positive)`
- `.balance-negative` Farbe `#b3261e` → `var(--color-balance-negative)`

**Step 4: Kalender-Farben**

Ersetze alle hartcodierten Kalender-Statusfarben in `.calendar-day-status-*`, `.month-day-*`, `.year-month-day-*` durch die entsprechenden `var(--color-cal-*)`.

**Step 5: Sonstige hartcodierte Werte**

- Backdrop-Overlay `rgba(13, 22, 35, 0.42)` → `var(--color-overlay)`
- Editing-Row `#eef3fb` → `var(--color-editing-row)`

**Step 6: Visuell prüfen**

```bash
cd frontend && npm run dev
```

Browser: Alle Seiten durchklicken, sicherstellen dass Farben identisch bleiben.

**Step 7: Commit**

```bash
git add frontend/src/components/ui.css frontend/src/theme/styles.css
git commit -m "refactor(ui): replace hardcoded colors with CSS custom properties"
```

---

### Task 1.4: Inline-Styles durch CSS-Klassen ersetzen

**Objective:** Alle 17 `style={{...}}` in Komponenten durch CSS-Klassen ersetzen.

**Files:**
- Modify: `frontend/src/components/ui.css`
- Modify: `frontend/src/pages/UnauthorizedPage.tsx`
- Modify: `frontend/src/pages/MyTimePage.tsx`
- Modify: `frontend/src/pages/SystemAdminPage.tsx`
- Modify: `frontend/src/pages/EmployeesPage.tsx`
- Modify: `frontend/src/components/QuickStampCard.tsx`
- Modify: `frontend/src/components/common.tsx`

**Step 1: Neue Utility-Klassen in ui.css hinzufügen**

```css
/* Utility: Spacing */
.section-gap { margin-top: var(--space-md); }
.section-gap-sm { margin-top: var(--space-sm); }
.section-gap-lg { margin-top: var(--space-lg); }

/* Utility: Layout */
.flex-row { display: flex; gap: var(--space-sm); }
.flex-between { display: flex; justify-content: space-between; }
.full-span { grid-column: 1 / -1; }
.centered-card { max-width: 560px; margin: var(--space-2xl) auto; }
.meta-reset { margin: 0; }

/* Utility: Typography */
.heading-lg { font-size: var(--text-xl); font-weight: 600; }
```

**Step 2: Jede Komponente aktualisieren**

Beispiel `UnauthorizedPage.tsx`:
```tsx
// Vorher:
<section className="card" style={{ maxWidth: 560, margin: '4rem auto' }}>
// Nachher:
<section className="card centered-card">
```

Alle 17 Stellen analog umsetzen.

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "refactor(ui): replace inline styles with CSS utility classes"
```

---

### Task 1.5: CSS in Komponenten-Dateien aufteilen

**Objective:** Monolithische `ui.css` (1401 Zeilen) in logische Module aufteilen.

**Files:**
- Create: `frontend/src/theme/layout.css` (AppShell, sidebar, topbar, page)
- Create: `frontend/src/theme/forms.css` (app-form, employee-form, inline-form)
- Create: `frontend/src/theme/calendar.css` (DashboardMonthCalendar, month, year)
- Create: `frontend/src/theme/datagrid.css` (DataGrid, table styles)
- Create: `frontend/src/theme/components.css` (card, btn, status, badge, totals-bar, etc.)
- Modify: `frontend/src/components/ui.css` (wird zum Import-Hub, importiert die Module)
- Modify: `frontend/src/main.tsx` (Import anpassen falls nötig)

**Step 1: ui.css analysieren und Sektionen identifizieren**

Etwaige Sektionen:
- Layout: `.app-shell`, `.sidebar`, `.topbar`, `.main-region`, `.page`
- Forms: `.app-form`, `.app-form-field`, `.employee-form`, `.inline-form`
- Calendar: `.calendar-*`, `.month-calendar-*`, `.year-*`
- DataGrid: `.datagrid-*`, `.dg-*`
- Components: `.card`, `.btn`, `.status`, `.badge`, `.totals-bar`, `.loading-block`, `.error-state`
- Utilities: `.sr-only`, `.meta`, `.actions`, `.section-gap`

**Step 2: Sektionen in separate Dateien verschieben**

Jede neue Datei bekommt einen Header-Kommentar. Die `ui.css` wird zum Import-Hub:

```css
/* ui.css -- Import-Hub */
@import './layout.css';
@import './components.css';
@import './forms.css';
@import './datagrid.css';
@import './calendar.css';
```

**Step 3: Duplikate zwischen calendar/month/year konsolidieren**

Identifizierte Duplikate:
- `.calendar-day-status-dot` vs `.month-day-status-dot` → `.day-status-dot`
- Kalender-Tile-Hover-Effekte → `.day-tile:hover`
- Status-Text-Klassen zusammenführen

**Step 4: Sicherstellen, dass Build funktioniert**

```bash
cd frontend && npm run build
```

**Step 5: Visuell prüfen**

```bash
cd frontend && npm run dev
```

Alle Seiten durchklicken, sicherstellen dass Layout identisch bleibt.

**Step 6: Commit**

```bash
git add frontend/src/theme/ frontend/src/components/ui.css
git commit -m "refactor(ui): split monolithic ui.css into component modules"
```

---

### Task 1.6: employee-form durch app-form ersetzen

**Objective:** Duplikat `employee-form-*`-Klassen entfernen, `app-form`-Pattern vereinheitlichen.

**Files:**
- Modify: `frontend/src/pages/EmployeesPage.tsx`
- Modify: `frontend/src/theme/forms.css` (nach Task 1.5)

**Step 1: EmployeesPage-Klassen umbenennen**

Ersetze in `EmployeesPage.tsx`:
- `className="employee-form-field"` → `className="app-form-field"`
- `className="employee-form-field employee-form-field-wide"` → `className="app-form-field app-form-field-wide"`
- `className="employee-form-toggle"` → eigene Klasse oder `app-form-field` mit Checkbox-Pattern
- `className="employee-form-overrides"` → `app-form-overrides`
- `className="employee-form-weekdays"` → `app-form-weekdays`
- `className="employee-form-actions"` → `actions`
- `className="employee-form-feedback"` → entfernen (inline-error/meta reicht)

**Step 2: employee-form-CSS-Regeln migrieren**

Übernehme nur die Regeln aus `employee-form`, die es in `app-form` noch nicht gibt (z.B. Wochentag-Checkbox-Layout), als Erweiterung von `app-form`.

**Step 3: Alte employee-form-CSS-Regeln löschen**

**Step 4: Visuell prüfen**

EmployeesPage im Browser testen, sicherstellen dass das Formular identisch aussieht.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "refactor(ui): unify employee-form into app-form pattern"
```

---

## Phase 2: i18n-Grundlagen und Sprachkonsistenz

### Task 2.1: i18n-Konstanten-Map erstellen und alle Labels konsolidieren

**Objective:** Alle UI-Texte an einem zentralen Ort definieren, Deutsch als Standardsprache.

**Files:**
- Create: `frontend/src/i18n/de.ts`
- Create: `frontend/src/i18n/index.ts`

**Step 1: i18n/de.ts erstellen**

```typescript
export const de = {
  nav: {
    dashboard: 'Dashboard',
    myTime: 'Zeitkonto',
    day: 'Tag',
    week: 'Woche',
    month: 'Monat',
    year: 'Jahr',
    employees: 'Mitarbeitende',
    workingTimeModels: 'Arbeitszeitmodelle',
    holidaySets: 'Feiertagssätze',
    holidays: 'Feiertage',
    nonWorkingPeriods: 'Arbeitsfreie Zeiträume',
    absences: 'Abwesenheiten',
    systemAdmin: 'Systemverwaltung',
  },
  actions: {
    save: 'Speichern',
    cancel: 'Abbrechen',
    delete: 'Löschen',
    edit: 'Bearbeiten',
    add: 'Hinzufügen',
    confirm: 'Bestätigen',
    reset: 'Zurücksetzen',
    login: 'Anmelden',
  },
  status: {
    complete: 'Vollständig',
    incomplete: 'Unvollständig',
    invalid: 'Ungültig',
    empty: 'Keine Daten',
    noData: 'Keine Daten',
  },
  pagination: {
    previous: 'Zurück',
    next: 'Weiter',
    perPage: 'pro Seite',
  },
  // ... weitere Kategorien nach Bedarf
} as const;

export type I18nKey = keyof typeof de;
```

**Step 2: i18n/index.ts als einfachen Hook**

```typescript
import { de } from './de';

export function t(key: string): string {
  const keys = key.split('.');
  let current: unknown = de;
  for (const k of keys) {
    if (current && typeof current === 'object' && k in current) {
      current = (current as Record<string, unknown>)[k];
    } else {
      return key; // Fallback: Key als Text
    }
  }
  return typeof current === 'string' ? current : key;
}

export { de };
```

**Step 3: Commit**

```bash
git add frontend/src/i18n/
git commit -m "feat(i18n): add German label constants map"
```

---

### Task 2.2: Navigation und Buttons auf Deutsch umstellen

**Objective:** Navigation, InlineEditActions, DataGrid-Paginierung und alle gemischten Labels auf Deutsch.

**Files:**
- Modify: `frontend/src/auth/roleRouting.ts`
- Modify: `frontend/src/components/InlineEditActions.tsx`
- Modify: `frontend/src/components/DataGrid.tsx`
- Modify: `frontend/src/components/common.tsx`

**Step 1: roleRouting.ts -- englische Labels ersetzen**

```typescript
import { t } from '../i18n';

// In den Nav-Items:
{ label: t('nav.day'), path: '/day' },
{ label: t('nav.week'), path: '/week' },
// etc.
```

**Step 2: InlineEditActions.tsx -- Save/Cancel ersetzen**

```typescript
import { t } from '../i18n';
// "Save" → t('actions.save')
// "Cancel" → t('actions.cancel')
```

**Step 3: DataGrid.tsx -- Paginierung ersetzen**

```typescript
import { t } from '../i18n';
// "Previous" → t('pagination.previous')
// "Next" → t('pagination.next')
// "{size} / page" → `${size} ${t('pagination.perPage')}`
```

**Step 4: Visuell prüfen**

Alle Seiten im Browser prüfen, sicherstellen dass Labels konsistent Deutsch sind.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat(i18n): switch nav, buttons and pagination to German labels"
```

---

## Phase 3: Barrierefreiheit

### Task 3.1: ConfirmDialog-Komponente erstellen

**Objective:** `window.confirm()` durch eine zugängliche, gestylte Dialog-Komponente ersetzen.

**Files:**
- Create: `frontend/src/components/ConfirmDialog.tsx`
- Create: `frontend/src/components/ConfirmDialog.css`
- Modify: `frontend/src/theme/components.css` (Backdrop-Overlay aufnehmen)

**Step 1: ConfirmDialog.tsx erstellen**

```tsx
import { useEffect, useRef } from 'react';
import { t } from '../i18n';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open, title, message,
  confirmLabel = t('actions.confirm'),
  cancelLabel = t('actions.cancel'),
  variant = 'default',
  onConfirm, onCancel,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      dialogRef.current?.showModal();
      confirmRef.current?.focus();
    } else {
      dialogRef.current?.close();
    }
  }, [open]);

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog"
      role="alertdialog"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      onClose={onCancel}
    >
      <h3 id="confirm-dialog-title">{title}</h3>
      <p id="confirm-dialog-message">{message}</p>
      <div className="confirm-dialog-actions">
        <button className="btn" onClick={onCancel}>{cancelLabel}</button>
        <button className={`btn ${variant === 'danger' ? 'danger' : ''}`} onClick={onConfirm} ref={confirmRef}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
```

**Step 2: ConfirmDialog.css erstellen**

```css
.confirm-dialog {
  border: none;
  border-radius: var(--radius);
  padding: var(--space-lg);
  max-width: 420px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.confirm-dialog::backdrop {
  background: var(--color-overlay);
}
.confirm-dialog h3 {
  margin: 0 0 var(--space-sm);
}
.confirm-dialog p {
  margin: 0 0 var(--space-lg);
  color: var(--muted);
}
.confirm-dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/ConfirmDialog.tsx frontend/src/components/ConfirmDialog.css
git commit -m "feat(ui): add accessible ConfirmDialog component"
```

---

### Task 3.2: window.confirm() durch ConfirmDialog ersetzen

**Objective:** Alle 6 `window.confirm()`-Aufrufe durch die neue Komponente ersetzen.

**Files:**
- Modify: `frontend/src/pages/DayPage.tsx`
- Modify: `frontend/src/pages/WorkingTimeModelsPage.tsx`
- Modify: `frontend/src/pages/NonWorkingPeriodSetsPage.tsx`
- Modify: `frontend/src/pages/HolidaySetsPage.tsx`
- Modify: `frontend/src/pages/HolidaysPage.tsx`

**Step 1: In jeder Page einen ConfirmDialog-State einführen**

```tsx
const [confirmDelete, setConfirmDelete] = useState<{ id: number; name: string } | null>(null);
```

**Step 2: window.confirm durch State-Steuerung ersetzen**

Beispiel DayPage:
```tsx
// Vorher:
const confirmed = window.confirm('Wirklich löschen?');
if (!confirmed) return;

// Nachher:
setConfirmDelete({ id: stamp.id, name: 'Zeitevent' });
// ... onConfirm handler führt die Mutation aus
```

**Step 3: ConfirmDialog in JSX einfügen**

```tsx
<ConfirmDialog
  open={confirmDelete !== null}
  title="Löschen bestätigen"
  message={`„${confirmDelete?.name}" wirklich löschen?`}
  variant="danger"
  confirmLabel="Löschen"
  onConfirm={() => { deleteMutation.mutate(confirmDelete!.id); setConfirmDelete(null); }}
  onCancel={() => setConfirmDelete(null)}
/>
```

**Step 4: Jede Page einzeln testen**

Für jede geänderte Page: Lösch-Button klicken, sicherstellen dass Dialog erscheint und funktioniert.

**Step 5: Commit**

```bash
git add frontend/src/pages/
git commit -m "refactor(ui): replace window.confirm with ConfirmDialog component"
```

---

### Task 3.3: Skip-to-Content-Link und html lang-Attribut

**Objective:** Keyboard-Navigation und Sprach-Attribut verbessern.

**Files:**
- Modify: `frontend/src/layout/AppShell.tsx`
- Modify: `frontend/index.html`

**Step 1: html lang-Attribut**

In `frontend/index.html`:
```html
<html lang="de">
```

**Step 2: Skip-to-Content-Link in AppShell**

Als erstes Element in AppShell, vor dem Sidebar-Grid:

```tsx
<a href="#main-content" className="skip-link">
  Zum Hauptinhalt springen
</a>
```

**Step 3: Skip-Link-CSS in layout.css**

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  background: var(--primary);
  color: #fff;
  padding: var(--space-sm) var(--space-md);
  z-index: 1000;
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  font-weight: 600;
}
.skip-link:focus {
  top: 0;
}
```

**Step 4: main-content-ID setzen**

In AppShell, `<main>`-Element:
```tsx
<main id="main-content" className="main-region">
```

**Step 5: Commit**

```bash
git add frontend/src/layout/AppShell.tsx frontend/src/theme/layout.css frontend/index.html
git commit -m "feat(a11y): add skip-to-content link and html lang attribute"
```

---

### Task 3.4: Form-Label-Assoziationen verbessern

**Objective:** Alle Form-Labels mit `htmlFor`/`id` verknüpfen.

**Files:**
- Modify: `frontend/src/pages/AdminAbsencesPage.tsx`
- Modify: `frontend/src/pages/NonWorkingPeriodSetsPage.tsx`
- Modify: `frontend/src/pages/HolidaysPage.tsx`
- Modify: `frontend/src/pages/HolidaySetsPage.tsx`
- Modify: `frontend/src/pages/WorkingTimeModelsPage.tsx`

**Step 1: Pro Page alle `<label>`-Elemente identifizieren**

Beispiel AdminAbsencesPage:
```tsx
// Vorher:
<label>Typ<select ...></select></label>

// Nachher:
<label htmlFor="absence-type">Typ</label>
<select id="absence-type" ...></select>
```

**Step 2: Alle Form-Elemente systematisch durchgehen**

Jede Admin-Page prüfen und `id`/`htmlFor`-Paare ergänzen.

**Step 3: Visuell prüfen**

Jede Form-Page testen, Label-Klick muss das Eingabefeld fokussieren.

**Step 4: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat(a11y): add htmlFor/id associations to all form labels"
```

---

## Phase 4: UX-Verbesserungen

### Task 4.1: NotFoundPage verbessern

**Objective:** NotFoundPage mit Heading und Dashboard-Link versehen.

**Files:**
- Modify: `frontend/src/pages/NotFoundPage.tsx`

**Step 1: NotFoundPage.tsx aktualisieren**

```tsx
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="card centered-card" role="alert">
      <h1 style={{ fontSize: 'var(--text-xl)', margin: 0 }}>Seite nicht gefunden</h1>
      <p className="meta" style={{ marginTop: 'var(--space-sm)' }}>
        Die angeforderte Seite existiert nicht oder wurde verschoben.
      </p>
      <div className="actions" style={{ marginTop: 'var(--space-md)' }}>
        <Link to="/dashboard" className="btn">Zum Dashboard</Link>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/pages/NotFoundPage.tsx
git commit -m "feat(ui): improve NotFoundPage with heading and dashboard link"
```

---

### Task 4.2: SystemAdminPage -- Bestaetigung fuer Rollenaenderungen

**Objective:** Dropdown-Rollenwechsel erfordert eine Bestaetigung vor der Mutation.

**Files:**
- Modify: `frontend/src/pages/SystemAdminPage.tsx`

**Step 1: State fuer Rollen-Bestaetigung einfuegen**

```tsx
const [pendingRoleChange, setPendingRoleChange] = useState<{ userId: number; newRole: string; userName: string } | null>(null);
```

**Step 2: Dropdown-Change zwischenspeichern statt sofort mutieren**

```tsx
<select
  value={user.role}
  onChange={(e) => setPendingRoleChange({ userId: user.id, newRole: e.target.value, userName: user.email })}
>
```

**Step 3: ConfirmDialog einsetzen**

```tsx
<ConfirmDialog
  open={pendingRoleChange !== null}
  title="Rolle ändern"
  message={`Rolle für ${pendingRoleChange?.userName} auf "${pendingRoleChange?.newRole}" ändern?`}
  variant="warning"
  confirmLabel="Rolle ändern"
  onConfirm={() => { roleUpdateMutation.mutate(...); setPendingRoleChange(null); }}
  onCancel={() => setPendingRoleChange(null)}
/>
```

**Step 4: Commit**

```bash
git add frontend/src/pages/SystemAdminPage.tsx
git commit -m "feat(ui): add confirmation for role changes in system admin"
```

---

### Task 4.3: DataGrid -- rowKey statt rowIndex

**Objective:** Eindeutige Keys fuer DataGrid-Zeilen.

**Files:**
- Modify: `frontend/src/components/DataGrid.tsx`

**Step 1: rowId-Prop einfuegen**

```tsx
interface DataGridProps<T> {
  // ... bestehende Props
  rowId?: (row: T) => string | number;
}
```

**Step 2: Key-Zuweisung anpassen**

```tsx
// Vorher:
<tr key={rowIndex}>

// Nachher:
<tr key={rowId ? rowId(row) : rowIndex}>
```

**Step 3: Alle DataGrid-Verwendungen aktualisieren**

In allen Pages die `rowId`-Prop ergaenzen, z.B.:
```tsx
<DataGrid columns={...} data={...} rowId={(row) => row.id} />
```

**Step 4: Commit**

```bash
git add frontend/src/components/DataGrid.tsx frontend/src/pages/
git commit -m "refactor(ui): add rowId prop to DataGrid for stable keys"
```

---

### Task 4.4: Toast-Benachrichtigungen einfuehren

**Objective:** Erfolg- und Fehler-Feedback fuer Mutationen.

**Files:**
- Create: `frontend/src/components/Toast.tsx`
- Create: `frontend/src/components/Toast.css`
- Modify: `frontend/src/main.tsx` (Toast-Container)

**Step 1: Toast-Komponente erstellen**

Einfacher Toast-Provider mit `useToast`-Hook:
- Position: Unten rechts
- Auto-Dismiss nach 3s
- Varianten: success, error, info
- `role="status"` + `aria-live="polite"`

**Step 2: Toast.CSS**

```css
.toast-container {
  position: fixed;
  bottom: var(--space-lg);
  right: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  z-index: 9999;
}
.toast {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  font-size: var(--text-sm);
}
.toast.success { border-left: 4px solid var(--success); }
.toast.error { border-left: 4px solid var(--danger); }
.toast.info { border-left: 4px solid var(--primary); }
```

**Step 3: Toasts bei Mutationen nutzen**

Beispiel DayPage Loesch-Mutation:
```tsx
deleteMutation.mutate(id, {
  onSuccess: () => toast.success('Zeitevent gelöscht'),
  onError: () => toast.error('Löschen fehlgeschlagen'),
});
```

**Step 4: Commit**

```bash
git add frontend/src/components/Toast.tsx frontend/src/components/Toast.css frontend/src/main.tsx
git commit -m "feat(ui): add toast notification system"
```

---

## Phase 5: Responsive und visuelle Feinheiten

### Task 5.1: Hamburger-Icon durch SVG ersetzen

**Objective:** Unicode `☰` / `✕` durch saubere SVG-Icons ersetzen.

**Files:**
- Modify: `frontend/src/layout/AppShell.tsx`

**Step 1: SVG-Icons erstellen**

```tsx
const MenuIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
);

const CloseIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
```

**Step 2: In AppShell ersetzen**

```tsx
// Vorher:
{menuOpen ? '✕' : '☰'}

// Nachher:
{menuOpen ? <CloseIcon /> : <MenuIcon />}
```

**Step 3: Commit**

```bash
git add frontend/src/layout/AppShell.tsx
git commit -m "feat(ui): replace unicode hamburger with SVG icons"
```

---

### Task 5.2: Status-Punkte bei Mobile sicherstellen (nicht nur Farbe)

**Objective:** Kalender-Status-Punkte auch bei kleinen Viewports mit Text-Alternative versehen.

**Files:**
- Modify: `frontend/src/components/ui.css` (bzw. `calendar.css` nach Phase 1)

**Step 1: calendar-day-status-text sicherstellen**

Aktuell wird `.calendar-day-status-text` bei `max-width: 1024px` auf `display: none` gesetzt.
Aendern zu:

```css
@media (max-width: 1024px) {
  .calendar-day-status-text {
    /* Statt display:none, kuerzeren Text zeigen */
    font-size: var(--text-xs);
  }
}
```

Oder: Die `aria-label` auf den Buttons enthalten bereits den Status-Text. Pruefen ob das ausreicht (screenreader bekommt den Text, nur visuell fehlt er). Falls ja, ist die `aria-hidden="true"` auf dem Dot korrekt, aber der sichtbare Text-Teil sollte bleiben.

**Step 2: Visuell bei 1024px und darunter pruefen**

**Step 3: Commit**

```bash
git add frontend/src/theme/calendar.css
git commit -m "fix(a11y): keep status text visible on mobile calendar"
```

---

## Zusammenfassung

| Phase | Tasks | Aufwand (Schaetzung) |
|-------|-------|----------------------|
| 1: Design-Tokens & CSS | 1.1-1.6 | ~4h |
| 2: i18n & Sprachkonsistenz | 2.1-2.2 | ~2h |
| 3: Barrierefreiheit | 3.1-3.4 | ~3h |
| 4: UX-Verbesserungen | 4.1-4.4 | ~3h |
| 5: Responsive & visuell | 5.1-5.2 | ~1h |
| **Total** | **16 Tasks** | **~13h** |

Jede Phase ist eigenstaendig deploybar. Die Reihenfolge ist empfohlen (Phase 1 zuerst, da nachfolgende Phasen die Token-Grundlage nutzen), aber nicht zwingend.

**Abhaengigkeiten:**
- Task 1.5 (CSS-Aufteilung) sollte vor 1.6 (employee-form) kommen
- Task 3.2 (window.confirm ersetzen) braucht Task 3.1 (ConfirmDialog)
- Task 4.4 (Toast) kann unabhaengig, profitiert aber von Task 1.3 (CSS-Variablen)