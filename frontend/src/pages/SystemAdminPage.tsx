import { FormEvent, useMemo, useState } from 'react';

import { ApiError } from '../api/client';
import { DataSection, EmptyState, ErrorState, LoadingBlock, PageHeader } from '../components/common';
import type { DataGridColumn } from '../components/DataGrid';
import { DataGrid } from '../components/DataGrid';
import { useAuth } from '../auth/provider';
import {
  useCreateSystemTenantMutation,
  useSystemTenants,
  useSystemUsers,
  useUpdateSystemTenantMutation,
  useUpdateSystemUserMutation,
} from '../hooks/useZytlogApi';
import type { SystemTenant, SystemUser, TenantType, UserRole } from '../types/api';

const tenantTypes: TenantType[] = ['company', 'demo'];
const userRoles: UserRole[] = ['system_admin', 'admin', 'team_lead', 'employee'];

type TenantFormState = {
  name: string;
  slug: string;
  active: boolean;
  type: TenantType;
  timezone: string;
};

const createTenantFormState = (): TenantFormState => ({
  name: '',
  slug: '',
  active: true,
  type: 'company',
  timezone: 'Europe/Zurich',
});

export function SystemAdminPage() {
  const { user } = useAuth();
  const isSystemAdmin = user?.role === 'system_admin';
  const tenantsQuery = useSystemTenants(isSystemAdmin);
  const usersQuery = useSystemUsers(isSystemAdmin);
  const createTenantMutation = useCreateSystemTenantMutation();
  const updateTenantMutation = useUpdateSystemTenantMutation();
  const updateUserMutation = useUpdateSystemUserMutation();

  const [tenantForm, setTenantForm] = useState<TenantFormState>(() => createTenantFormState());
  const [editingTenantId, setEditingTenantId] = useState<number | null>(null);
  const [tenantError, setTenantError] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  const tenantsById = useMemo(
    () => new Map((tenantsQuery.data ?? []).map((tenant) => [tenant.id, tenant.name])),
    [tenantsQuery.data],
  );

  const tenantColumns = useMemo<DataGridColumn<SystemTenant>[]>(
    () => [
      { id: 'name', header: 'Tenant', cell: (row) => row.name, searchableText: (row) => `${row.name} ${row.slug}`, sortable: true, sortValue: (row) => row.name },
      { id: 'slug', header: 'Slug', cell: (row) => row.slug, sortable: true, sortValue: (row) => row.slug },
      { id: 'type', header: 'Typ', cell: (row) => row.type },
      { id: 'timezone', header: 'Timezone', cell: (row) => row.timezone },
      { id: 'active', header: 'Aktiv', cell: (row) => (row.active ? 'Ja' : 'Nein') },
      {
        id: 'actions',
        header: 'Aktion',
        cell: (row) => (
          <button
            type="button"
            className="btn outline"
            onClick={() => {
              setEditingTenantId(row.id);
              setTenantForm({
                name: row.name,
                slug: row.slug,
                active: row.active,
                type: row.type,
                timezone: row.timezone,
              });
              setTenantError(null);
            }}
          >
            Bearbeiten
          </button>
        ),
      },
    ],
    [],
  );

  const userColumns = useMemo<DataGridColumn<SystemUser>[]>(
    () => [
      { id: 'full_name', header: 'Name', cell: (row) => row.full_name, searchableText: (row) => `${row.full_name} ${row.email}`, sortable: true, sortValue: (row) => row.full_name },
      { id: 'email', header: 'E-Mail', cell: (row) => row.email, searchableText: (row) => row.email },
      {
        id: 'tenant',
        header: 'Tenant',
        cell: (row) => (row.role === 'system_admin' ? 'Systemweit' : (tenantsById.get(row.tenant_id) ?? `#${row.tenant_id}`)),
      },
      { id: 'role', header: 'Rolle', cell: (row) => row.role },
      { id: 'employee_profile', header: 'Mitarbeiterprofil', cell: (row) => (row.has_employee_profile ? 'Ja' : 'Nein') },
      {
        id: 'role_action',
        header: 'Rolle ändern',
        cell: (row) => (
          <select
            value={row.role}
            onChange={async (event) => {
              setUserError(null);
              try {
                await updateUserMutation.mutateAsync({
                  userId: row.id,
                  payload: { role: event.target.value as UserRole },
                });
              } catch (error) {
                setUserError(error instanceof ApiError ? error.message : 'Rolle konnte nicht aktualisiert werden.');
              }
            }}
          >
            {userRoles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        ),
      },
      {
        id: 'tenant_action',
        header: 'Tenant ändern',
        cell: (row) => {
          if (row.role === 'system_admin') {
            return <span className="meta">Nicht verfügbar für system_admin</span>;
          }

          return (
            <select
              value={row.tenant_id}
              onChange={async (event) => {
                setUserError(null);
                try {
                  await updateUserMutation.mutateAsync({
                    userId: row.id,
                    payload: { tenant_id: Number(event.target.value) },
                  });
                } catch (error) {
                  setUserError(error instanceof ApiError ? error.message : 'Tenant konnte nicht aktualisiert werden.');
                }
              }}
            >
              {(tenantsQuery.data ?? []).map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </select>
          );
        },
      },
    ],
    [tenantsById, tenantsQuery.data, updateUserMutation],
  );

  const handleTenantSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setTenantError(null);

    const payload = {
      name: tenantForm.name,
      slug: tenantForm.slug,
      active: tenantForm.active,
      type: tenantForm.type,
      timezone: tenantForm.timezone,
      default_holiday_set_id: null,
    };

    try {
      if (editingTenantId) {
        await updateTenantMutation.mutateAsync({ tenantId: editingTenantId, payload });
      } else {
        await createTenantMutation.mutateAsync(payload);
      }
      setEditingTenantId(null);
      setTenantForm(createTenantFormState());
    } catch (error) {
      setTenantError(error instanceof ApiError ? error.message : 'Tenant konnte nicht gespeichert werden.');
    }
  };

  if (!isSystemAdmin) {
    return <EmptyState title="Nicht verfügbar" description="Diese Ansicht ist nur für system_admin sichtbar." />;
  }

  if (tenantsQuery.isLoading || usersQuery.isLoading) {
    return <LoadingBlock />;
  }

  if (tenantsQuery.isError) {
    return <ErrorState message={tenantsQuery.error instanceof Error ? tenantsQuery.error.message : 'Tenants konnten nicht geladen werden.'} />;
  }

  if (usersQuery.isError) {
    return <ErrorState message={usersQuery.error instanceof Error ? usersQuery.error.message : 'Users konnten nicht geladen werden.'} />;
  }

  return (
    <>
      <PageHeader title="Systemverwaltung" subtitle="Tenant- und Benutzerverwaltung für System-Administratoren" />

      <DataSection title={editingTenantId ? 'Tenant bearbeiten' : 'Tenant anlegen'}>
        <form className="form-grid" onSubmit={handleTenantSubmit}>
          <label>
            <span>Name</span>
            <input value={tenantForm.name} onChange={(event) => setTenantForm((current) => ({ ...current, name: event.target.value }))} required />
          </label>
          <label>
            <span>Slug</span>
            <input value={tenantForm.slug} onChange={(event) => setTenantForm((current) => ({ ...current, slug: event.target.value }))} required />
          </label>
          <label>
            <span>Typ</span>
            <select value={tenantForm.type} onChange={(event) => setTenantForm((current) => ({ ...current, type: event.target.value as TenantType }))}>
              {tenantTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Timezone</span>
            <input value={tenantForm.timezone} onChange={(event) => setTenantForm((current) => ({ ...current, timezone: event.target.value }))} required />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input type="checkbox" checked={tenantForm.active} onChange={(event) => setTenantForm((current) => ({ ...current, active: event.target.checked }))} />
            <span>Aktiv</span>
          </label>
          <div className="actions" style={{ gridColumn: '1 / -1' }}>
            <button type="submit" className="btn" disabled={createTenantMutation.isPending || updateTenantMutation.isPending}>
              {editingTenantId ? 'Tenant speichern' : 'Tenant anlegen'}
            </button>
            {editingTenantId ? (
              <button
                type="button"
                className="btn outline"
                onClick={() => {
                  setEditingTenantId(null);
                  setTenantForm(createTenantFormState());
                  setTenantError(null);
                }}
              >
                Abbrechen
              </button>
            ) : null}
          </div>
          {tenantError ? <div className="inline-error">{tenantError}</div> : null}
        </form>
      </DataSection>

      <DataSection title="Tenants">
        <DataGrid<SystemTenant>
          data={tenantsQuery.data ?? []}
          columns={tenantColumns}
          emptyTitle="Keine Tenants vorhanden"
          emptyDescription="Lege den ersten Tenant oben an."
        />
      </DataSection>

      <DataSection title="Interne Benutzer">
        {userError ? <div className="inline-error" style={{ marginBottom: '0.75rem' }}>{userError}</div> : null}
        <DataGrid<SystemUser>
          data={usersQuery.data ?? []}
          columns={userColumns}
          emptyTitle="Keine Benutzer vorhanden"
          emptyDescription="Sobald Benutzer sich anmelden oder manuell erstellt werden, erscheinen sie hier."
        />
      </DataSection>
    </>
  );
}
