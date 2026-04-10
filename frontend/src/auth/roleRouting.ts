import type { UserRole } from '../types/api';

export type NavItem = { to: string; label: string };

const employeeNavItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/my-time', label: 'Zeitkonto' },
  { to: '/day', label: 'Tag' },
  { to: '/week', label: 'Woche' },
  { to: '/month', label: 'Monat' },
  { to: '/year', label: 'Jahr' },
  { to: '/my-absences', label: 'Meine Abwesenheiten' },
];

const adminManagementNavItems: NavItem[] = [
  { to: '/employees', label: 'Mitarbeitende' },
  { to: '/working-time-models', label: 'Arbeitszeitmodelle' },
  { to: '/holiday-sets', label: 'Feiertagssätze' },
  { to: '/holidays', label: 'Feiertage' },
  { to: '/non-working-period-sets', label: 'Arbeitsfreie Zeiträume' },
  { to: '/admin-absences', label: 'Abwesenheiten' },
];

const adminNavItems: NavItem[] = [...employeeNavItems, ...adminManagementNavItems];

const systemAdminNavItems: NavItem[] = [{ to: '/system-admin', label: 'Systemverwaltung' }];

const managedAppPathPrefixes = [
  '/dashboard',
  '/my-time',
  '/day',
  '/week',
  '/month',
  '/year',
  '/my-absences',
  '/employees',
  '/working-time-models',
  '/holiday-sets',
  '/holidays',
  '/non-working-period-sets',
  '/admin-absences',
  '/system-admin',
] as const;

function matchesPath(pathname: string, routePath: string): boolean {
  return pathname === routePath || pathname.startsWith(`${routePath}/`);
}

export function getNavItemsByRole(role?: UserRole): NavItem[] {
  if (role === 'system_admin') return systemAdminNavItems;
  if (role === 'admin') return adminNavItems;
  return employeeNavItems;
}

export function getDefaultRouteForRole(role?: UserRole): string {
  return getNavItemsByRole(role)[0]?.to ?? '/dashboard';
}

export function isManagedAppPath(pathname: string): boolean {
  return managedAppPathPrefixes.some((prefix) => matchesPath(pathname, prefix));
}

export function isPathAllowedForRole(pathname: string, role?: UserRole): boolean {
  if (pathname === '/') {
    return true;
  }

  return getNavItemsByRole(role).some((item) => matchesPath(pathname, item.to));
}
