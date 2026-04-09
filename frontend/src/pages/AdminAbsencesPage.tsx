import { FormEvent, useState } from 'react';

import { ApiError } from '../api/client';
import { useAuth } from '../auth/provider';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import {
  useAdminAbsences,
  useCreateAdminAbsenceMutation,
  useDeleteAdminAbsenceMutation,
  useEmployees,
  useUpdateAdminAbsenceMutation,
} from '../hooks/useZytlogApi';

export function AdminAbsencesPage() {
  const { isAdmin } = useAuth();
  const [employeeId, setEmployeeId] = useState<number | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<{ employee_id: string; absence_type: 'vacation' | 'sickness'; start_date: string; end_date: string; duration_type: 'full_day' | 'half_day_am' | 'half_day_pm'; note: string }>({ employee_id: '', absence_type: 'vacation', start_date: '', end_date: '', duration_type: 'full_day', note: '' });

  const employees = useEmployees(isAdmin);
  const absences = useAdminAbsences(isAdmin, employeeId);
  const createMutation = useCreateAdminAbsenceMutation();
  const updateMutation = useUpdateAdminAbsenceMutation();
  const deleteMutation = useDeleteAdminAbsenceMutation();

  if (!isAdmin) return <EmptyState title="Nicht verfügbar" description="Nur Administratoren können Abwesenheiten verwalten." />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await createMutation.mutateAsync({ ...form, employee_id: Number(form.employee_id), note: form.note || null });
      setForm({ employee_id: '', absence_type: 'vacation', start_date: '', end_date: '', duration_type: 'full_day', note: '' });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Abwesenheit konnte nicht gespeichert werden.');
    }
  };

  return (
    <>
      <PageHeader title="Abwesenheiten" subtitle="Stage-1 Verwaltung für Vacation/Sickness" />
      <DataSection title="Abwesenheit anlegen">
        <form className="app-form" onSubmit={onSubmit}>
          <label>Mitarbeiter
            <select required value={form.employee_id} onChange={(e) => setForm((p) => ({ ...p, employee_id: e.target.value }))}>
              <option value="">Bitte wählen</option>
              {(employees.data ?? []).map((employee) => <option key={employee.id} value={employee.id}>{employee.first_name} {employee.last_name}</option>)}
            </select>
          </label>
          <label>Typ<select value={form.absence_type} onChange={(e) => setForm((p) => ({ ...p, absence_type: e.target.value as 'vacation' | 'sickness' }))}><option value="vacation">Vacation</option><option value="sickness">Sickness</option></select></label>
          <label>Von<input required type="date" value={form.start_date} onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))} /></label>
          <label>Bis<input required type="date" value={form.end_date} onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))} /></label>
          <label>Dauer<select value={form.duration_type} onChange={(e) => setForm((p) => ({ ...p, duration_type: e.target.value as 'full_day' | 'half_day_am' | 'half_day_pm' }))}><option value="full_day">Full day</option><option value="half_day_am">Half day AM</option><option value="half_day_pm">Half day PM</option></select></label>
          <label>Notiz<input value={form.note} onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))} /></label>
          <button type="submit" className="btn primary">Speichern</button>
          {error ? <p className="inline-error">{error}</p> : null}
        </form>
      </DataSection>
      <DataSection title="Vorhandene Abwesenheiten">
        <label>Filter Mitarbeiter
          <select value={employeeId ?? ''} onChange={(e) => setEmployeeId(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">Alle</option>
            {(employees.data ?? []).map((employee) => <option key={employee.id} value={employee.id}>{employee.first_name} {employee.last_name}</option>)}
          </select>
        </label>
        {absences.isLoading ? <LoadingBlock /> : null}
        {absences.error ? <ErrorState message="Abwesenheiten konnten nicht geladen werden." /> : null}
        <ul>
          {(absences.data ?? []).map((a) => (
            <li key={a.id}>
              #{a.id} Employee {a.employee_id} · {a.start_date}–{a.end_date} · {a.absence_type} ({a.duration_type})
              <button className="btn secondary" type="button" onClick={() => void updateMutation.mutateAsync({ absenceId: a.id, payload: { note: `${a.note ?? ''} (edited)` } })}>Schnell editieren</button>
              <button className="btn danger" type="button" onClick={() => void deleteMutation.mutateAsync(a.id)}>Löschen</button>
            </li>
          ))}
        </ul>
      </DataSection>
    </>
  );
}
