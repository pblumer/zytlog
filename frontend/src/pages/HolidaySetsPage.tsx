import { FormEvent, useEffect, useMemo, useState } from 'react';

import { useAuth } from '../auth/provider';
import { ApiError } from '../api/client';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import { DataGrid } from '../components/DataGrid';
import type { DataGridColumn } from '../components/DataGrid';
import { TableStatusBadge } from '../components/TableStatusBadge';
import {
  useCommitOpenHolidaysImportMutation,
  useCreateHolidaySetMutation,
  useDeleteHolidaySetMutation,
  useHolidaySets,
  useOpenHolidaysCountries,
  useOpenHolidaysLanguages,
  useOpenHolidaysSubdivisions,
  usePreviewOpenHolidaysImportMutation,
  useUpdateHolidaySetMutation,
} from '../hooks/useZytlogApi';
import type { HolidaySet, OpenHolidaysImportMode, OpenHolidaysImportPreviewRow } from '../types/api';

type HolidaySetFormState = {
  name: string;
  description: string;
  source: string;
  active: boolean;
};

type ImportFormState = {
  countryIsoCode: string;
  subdivisionCode: string;
  languageCode: string;
  validFrom: string;
  validTo: string;
  importMode: OpenHolidaysImportMode;
};

const defaultFormState: HolidaySetFormState = {
  name: '',
  description: '',
  source: 'manual',
  active: true,
};

const today = new Date();
const startOfYear = `${today.getUTCFullYear()}-01-01`;
const endOfYear = `${today.getUTCFullYear()}-12-31`;

const defaultImportState: ImportFormState = {
  countryIsoCode: 'CH',
  subdivisionCode: '',
  languageCode: 'DE',
  validFrom: startOfYear,
  validTo: endOfYear,
  importMode: 'skip_existing',
};

export function HolidaySetsPage() {
  const { isAdmin } = useAuth();
  const [editingHolidaySetId, setEditingHolidaySetId] = useState<number | null>(null);
  const [formState, setFormState] = useState<HolidaySetFormState>(defaultFormState);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const [selectedImportHolidaySet, setSelectedImportHolidaySet] = useState<HolidaySet | null>(null);
  const [importFormState, setImportFormState] = useState<ImportFormState>(defaultImportState);
  const [previewRows, setPreviewRows] = useState<OpenHolidaysImportPreviewRow[]>([]);
  const [importFeedback, setImportFeedback] = useState<string | null>(null);
  const [importSummary, setImportSummary] = useState<{ created: number; skipped: number; replaced: number } | null>(null);
  const [confirmDeleteSet, setConfirmDeleteSet] = useState<HolidaySet | null>(null);

  const query = useHolidaySets(isAdmin);
  const createMutation = useCreateHolidaySetMutation();
  const updateMutation = useUpdateHolidaySetMutation();
  const deleteMutation = useDeleteHolidaySetMutation();

  const countriesQuery = useOpenHolidaysCountries(isAdmin);
  const languagesQuery = useOpenHolidaysLanguages(isAdmin);
  const subdivisionsQuery = useOpenHolidaysSubdivisions(importFormState.countryIsoCode || null, isAdmin);
  const previewMutation = usePreviewOpenHolidaysImportMutation();
  const commitMutation = useCommitOpenHolidaysImportMutation();

  useEffect(() => {
    if (countriesQuery.data?.length && !countriesQuery.data.find((item) => item.iso_code === importFormState.countryIsoCode)) {
      setImportFormState((prev) => ({ ...prev, countryIsoCode: countriesQuery.data[0].iso_code }));
    }
  }, [countriesQuery.data, importFormState.countryIsoCode]);

  const columns = useMemo<DataGridColumn<HolidaySet>[]>(
    () => [
      { id: 'name', header: 'Name', cell: (row) => row.name, searchableText: (row) => row.name, sortable: true },
      {
        id: 'description',
        header: 'Beschreibung',
        cell: (row) => row.description ?? '—',
        searchableText: (row) => row.description ?? '',
      },
      { id: 'source', header: 'Quelle', cell: (row) => row.source ?? 'manuell' },
      { id: 'holiday_count', header: 'Feiertage', cell: (row) => row.holiday_count, sortable: true, sortValue: (row) => row.holiday_count },
      { id: 'active', header: 'Aktiv', cell: (row) => <TableStatusBadge status={row.active ? 'complete' : 'empty'} /> },
      {
        id: 'actions',
        header: 'Aktionen',
        cell: (row) => (
          <div className="actions">
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setSelectedImportHolidaySet(row);
                setPreviewRows([]);
                setImportFeedback(null);
              }}
            >
              Import aus OpenHolidays
            </button>
            <button
              type="button"
              className="btn outline"
              onClick={() => {
                setEditingHolidaySetId(row.id);
                setFormState({
                  name: row.name,
                  description: row.description ?? '',
                  source: row.source ?? 'manual',
                  active: row.active,
                });
                setMutationError(null);
              }}
            >
              Feiertagssatz bearbeiten
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={() => setConfirmDeleteSet(row)}
            >
              Feiertagssatz löschen
            </button>
          </div>
        ),
      },
    ],
    [deleteMutation],
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMutationError(null);
    const payload = {
      name: formState.name,
      description: formState.description || null,
      source: formState.source || null,
      country_code: null,
      region_code: null,
      active: formState.active,
    };

    try {
      if (editingHolidaySetId != null) {
        await updateMutation.mutateAsync({ holidaySetId: editingHolidaySetId, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setEditingHolidaySetId(null);
      setFormState(defaultFormState);
    } catch (error) {
      if (error instanceof ApiError) {
        setMutationError(error.message);
        return;
      }
      setMutationError('Feiertagssatz konnte nicht gespeichert werden.');
    }
  };

  const onPreviewImport = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedImportHolidaySet) return;
    setImportFeedback(null);
    setImportSummary(null);
    try {
      const response = await previewMutation.mutateAsync({
        holidaySetId: selectedImportHolidaySet.id,
        payload: {
          country_iso_code: importFormState.countryIsoCode,
          subdivision_code: importFormState.subdivisionCode || null,
          language_code: importFormState.languageCode,
          valid_from: importFormState.validFrom,
          valid_to: importFormState.validTo,
          import_mode: importFormState.importMode,
        },
      });
      setPreviewRows(response.rows);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.message.includes('Keine Feiertage')) {
          setImportFeedback('Für den gewählten Zeitraum wurden keine Feiertage gefunden.');
        } else if (error.message.includes('doppelte')) {
          setImportFeedback('Der Import enthielt doppelte Feiertage pro Datum und wurde nicht verarbeitet.');
        } else {
          setImportFeedback(error.message);
        }
      } else {
        setImportFeedback('Import-Vorschau konnte nicht geladen werden.');
      }
      setPreviewRows([]);
    }
  };

  const onCommitImport = async () => {
    if (!selectedImportHolidaySet) return;
    setImportFeedback(null);
    try {
      const response = await commitMutation.mutateAsync({
        holidaySetId: selectedImportHolidaySet.id,
        payload: {
          country_iso_code: importFormState.countryIsoCode,
          subdivision_code: importFormState.subdivisionCode || null,
          language_code: importFormState.languageCode,
          valid_from: importFormState.validFrom,
          valid_to: importFormState.validTo,
          import_mode: importFormState.importMode,
        },
      });
      setImportSummary(response);
      setImportFeedback(null);
      setPreviewRows([]);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          setImportFeedback('Beim Import sind Konflikte mit bereits vorhandenen Feiertagen aufgetreten.');
        } else {
          setImportFeedback(error.message);
        }
      } else {
        setImportFeedback('Import konnte nicht durchgeführt werden.');
      }
    }
  };

  if (!isAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Feiertagssätze sind nur für Administratoren sichtbar." />;
  }

  const handleConfirmDeleteSet = async () => {
    if (!confirmDeleteSet) return;
    try {
      await deleteMutation.mutateAsync(confirmDeleteSet.id);
    } catch (error) {
      setMutationError(error instanceof Error ? error.message : 'Feiertagssatz konnte nicht gelöscht werden.');
    } finally {
      setConfirmDeleteSet(null);
    }
  };

  return (
    <>
      <PageHeader title="Feiertagssätze" subtitle="Wiederverwendbare Feiertagssätze pro Tenant verwalten" />
      <DataSection title={editingHolidaySetId ? 'Feiertagssatz bearbeiten' : 'Feiertagssatz anlegen'}>
        <form className="app-form" onSubmit={onSubmit}>
          <label htmlFor="hs-name">
            Name
            <input id="hs-name" value={formState.name} onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))} required />
          </label>
          <label htmlFor="hs-desc">
            Beschreibung
            <input id="hs-desc" value={formState.description} onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))} />
          </label>
          <label htmlFor="hs-source">
            Quelle
            <input id="hs-source" value={formState.source} onChange={(event) => setFormState((prev) => ({ ...prev, source: event.target.value }))} />
          </label>
          <label className="app-form-check">
            <input type="checkbox" checked={formState.active} onChange={(event) => setFormState((prev) => ({ ...prev, active: event.target.checked }))} /> Aktiv
          </label>
          <div className="actions">
            <button type="submit" className="btn primary">{editingHolidaySetId ? 'Änderungen speichern' : 'Feiertagssatz speichern'}</button>
          </div>
          {mutationError ? <p className="inline-error">{mutationError}</p> : null}
        </form>
      </DataSection>
      {selectedImportHolidaySet ? (
        <DataSection title={`OpenHolidays-Import für „${selectedImportHolidaySet.name}“`}>
          <form className="grid import-config-grid" onSubmit={onPreviewImport}>
            <div className="import-config-card">
              <p className="meta">1) Parameter auswählen</p>
              <div className="grid">
                <label htmlFor="hs-country">
                  Land
                  <select
                    id="hs-country"
                    value={importFormState.countryIsoCode}
                    onChange={(event) => setImportFormState((prev) => ({ ...prev, countryIsoCode: event.target.value, subdivisionCode: '' }))}
                  >
                    {(countriesQuery.data ?? []).map((country) => (
                      <option key={country.iso_code} value={country.iso_code}>
                        {country.iso_code} {country.name ? `— ${country.name}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <label htmlFor="hs-subdivision">
                  Region / Subdivision
                  <select
                    id="hs-subdivision"
                    value={importFormState.subdivisionCode}
                    onChange={(event) => setImportFormState((prev) => ({ ...prev, subdivisionCode: event.target.value }))}
                  >
                    <option value="">Keine regionale Einschränkung</option>
                    {(subdivisionsQuery.data ?? []).map((subdivision) => (
                      <option key={subdivision.code} value={subdivision.code}>
                        {subdivision.code} {subdivision.name ? `— ${subdivision.name}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <label htmlFor="hs-language">
                  Sprache
                  <select
                    id="hs-language"
                    value={importFormState.languageCode}
                    onChange={(event) => setImportFormState((prev) => ({ ...prev, languageCode: event.target.value }))}
                  >
                    {(languagesQuery.data ?? []).map((language) => (
                      <option key={language.language_code} value={language.language_code}>
                        {language.language_code.toUpperCase()} {language.name ? `— ${language.name}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <label htmlFor="hs-valid-from">
                  Gültig von
                  <input id="hs-valid-from" type="date" value={importFormState.validFrom} onChange={(event) => setImportFormState((prev) => ({ ...prev, validFrom: event.target.value }))} required />
                </label>
                <label htmlFor="hs-valid-to">
                  Gültig bis
                  <input id="hs-valid-to" type="date" value={importFormState.validTo} onChange={(event) => setImportFormState((prev) => ({ ...prev, validTo: event.target.value }))} required />
                </label>
                <label htmlFor="hs-import-mode">
                  Importmodus
                  <select
                    id="hs-import-mode"
                    value={importFormState.importMode}
                    onChange={(event) => setImportFormState((prev) => ({ ...prev, importMode: event.target.value as OpenHolidaysImportMode }))}
                  >
                    <option value="skip_existing">Bestehende Feiertage überspringen</option>
                    <option value="replace_existing_in_range">Bestehende Feiertage im Zeitraum ersetzen</option>
                  </select>
                </label>
              </div>
              {subdivisionsQuery.error ? (
                <p className="inline-warning">Regionen/Subdivisions konnten nicht geladen werden. Sie können den Import ohne regionale Einschränkung fortsetzen.</p>
              ) : null}
              <div className="actions">
                <button type="submit" className="btn primary" disabled={previewMutation.isPending || countriesQuery.isLoading || languagesQuery.isLoading}>
                  Vorschau laden
                </button>
              </div>
            </div>
          </form>
          {previewRows.length > 0 ? (
            <div className="import-preview-card">
              <p className="meta">2) Vorschau prüfen</p>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Datum</th>
                      <th>Name</th>
                      <th>Bereits vorhanden</th>
                      <th>Geplante Aktion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row) => (
                      <tr key={row.date}>
                        <td>{row.date}</td>
                        <td>{row.name}</td>
                        <td>{row.exists_in_holiday_set ? 'Ja' : 'Nein'}</td>
                        <td>{row.action_hint}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="actions">
                <button
                  type="button"
                  className="btn primary"
                  disabled={commitMutation.isPending || previewRows.length === 0}
                  onClick={onCommitImport}
                >
                  Import bestätigen
                </button>
              </div>
            </div>
          ) : null}
          {importFeedback ? <p className="inline-error">{importFeedback}</p> : null}
          {importSummary ? (
            <p className="meta">
              Import abgeschlossen — Erstellt: {importSummary.created}, Übersprungen: {importSummary.skipped}, Ersetzt: {importSummary.replaced}
            </p>
          ) : null}
        </DataSection>
      ) : null}
      <DataSection title="Feiertagssätze">
        {query.isLoading ? <LoadingBlock /> : null}
        {query.error ? <ErrorState message="Feiertagssätze konnten nicht geladen werden." /> : null}
        {query.data ? <DataGrid columns={columns} data={query.data} searchPlaceholder="Feiertagssätze suchen…" rowId={(row) => row.id} /> : null}
      </DataSection>
      <ConfirmDialog
        open={confirmDeleteSet !== null}
        title="Feiertagssatz löschen"
        message={confirmDeleteSet ? `Feiertagssatz „${confirmDeleteSet.name}“ löschen?` : ''}
        confirmLabel="Löschen"
        variant="danger"
        onConfirm={() => void handleConfirmDeleteSet()}
        onCancel={() => setConfirmDeleteSet(null)}
      />
    </>
  );
}
