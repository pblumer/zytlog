import { FormEvent, useState } from 'react';

import { ApiError } from '../api/client';
import { DataSection, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import { useCreateMyAbsenceMutation, useMyAbsences } from '../hooks/useZytlogApi';

export function MyAbsencesPage() {
  const [form, setForm] = useState<{ absence_type: 'vacation' | 'sickness'; start_date: string; end_date: string; duration_type: 'full_day' | 'half_day_am' | 'half_day_pm'; note: string }>({ absence_type: 'vacation', start_date: '', end_date: '', duration_type: 'full_day', note: '' });
  const [error, setError] = useState<string | null>(null);
  const query = useMyAbsences();
  const createMutation = useCreateMyAbsenceMutation();

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await createMutation.mutateAsync({ ...form, note: form.note || null });
      setForm({ absence_type: 'vacation', start_date: '', end_date: '', duration_type: 'full_day', note: '' });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Abwesenheit konnte nicht angelegt werden.');
    }
  };

  return (
    <>
      <PageHeader title="My Absences" subtitle="Eigene Abwesenheiten erfassen und einsehen" />
      <DataSection title="Neue Abwesenheit">
        <form className="app-form" onSubmit={onSubmit}>
          <label>Typ
            <select value={form.absence_type} onChange={(e) => setForm((p) => ({ ...p, absence_type: e.target.value as 'vacation' | 'sickness' }))}>
              <option value="vacation">Vacation</option>
              <option value="sickness">Sickness</option>
            </select>
          </label>
          <label>Von<input type="date" required value={form.start_date} onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))} /></label>
          <label>Bis<input type="date" required value={form.end_date} onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))} /></label>
          <label>Dauer
            <select value={form.duration_type} onChange={(e) => setForm((p) => ({ ...p, duration_type: e.target.value as 'full_day' | 'half_day_am' | 'half_day_pm' }))}>
              <option value="full_day">Full day</option>
              <option value="half_day_am">Half day AM</option>
              <option value="half_day_pm">Half day PM</option>
            </select>
          </label>
          <label>Notiz<input value={form.note} onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))} /></label>
          <button className="btn primary" type="submit">Abwesenheit speichern</button>
          {error ? <p className="inline-error">{error}</p> : null}
        </form>
      </DataSection>
      <DataSection title="Meine Abwesenheiten">
        {query.isLoading ? <LoadingBlock /> : null}
        {query.error ? <ErrorState message="Abwesenheiten konnten nicht geladen werden." /> : null}
        <ul>
          {(query.data ?? []).map((a) => (
            <li key={a.id}>{a.start_date} – {a.end_date}: {a.absence_type} ({a.duration_type})</li>
          ))}
        </ul>
      </DataSection>
    </>
  );
}
