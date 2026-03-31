import { NavLink, Outlet, type NavLinkRenderProps } from 'react-router-dom';

import { useAuth } from '../auth/provider';
import type { UserRole } from '../types/api';

type NavItem = { to: string; label: string };

const employeeNavItems: NavItem[] = [
  { to: '/', label: 'Dashboard' },
  { to: '/my-time', label: 'My Time' },
  { to: '/day', label: 'Day' },
  { to: '/week', label: 'Week' },
  { to: '/month', label: 'Month' },
  { to: '/year', label: 'Year' },
  { to: '/my-absences', label: 'My Absences' },
];

const adminNavItems: NavItem[] = [
  { to: '/employees', label: 'Employees' },
  { to: '/working-time-models', label: 'Working Time Models' },
  { to: '/holiday-sets', label: 'Feiertagssätze' },
  { to: '/holidays', label: 'Feiertage' },
  { to: '/non-working-period-sets', label: 'Arbeitsfreie Zeiträume' },
  { to: '/admin-absences', label: 'Abwesenheiten' },
];

function getNavItemsByRole(role?: UserRole): NavItem[] {
  if (role === 'admin') return adminNavItems;
  return employeeNavItems;
}

export function AppShell() {
  const { user, logout } = useAuth();
  const navItems = getNavItemsByRole(user?.role);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Zytlog</div>
        <ul className="nav-list">
          {user?.role === 'admin' ? <li className="meta">Verwaltung</li> : null}
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink to={item.to} end={item.to === '/'} className={({ isActive }: NavLinkRenderProps) => `nav-link${isActive ? ' active' : ''}`}>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </aside>

      <div className="main-region">
        <header className="topbar">
          <div>
            <strong>{user?.username ?? user?.email}</strong>
            <div className="meta">Role: {user?.role ?? 'unknown'}</div>
          </div>
          <button className="btn outline" onClick={logout}>
            Logout
          </button>
        </header>

        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
