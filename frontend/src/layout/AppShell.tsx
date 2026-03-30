import { NavLink, Outlet, type NavLinkRenderProps } from 'react-router-dom';

import { useAuth } from '../auth/provider';

type NavItem = { to: string; label: string; admin?: boolean };

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard' },
  { to: '/my-time', label: 'My Time' },
  { to: '/day', label: 'Day' },
  { to: '/week', label: 'Week' },
  { to: '/month', label: 'Month' },
  { to: '/year', label: 'Year' },
  { to: '/employees', label: 'Employees', admin: true },
  { to: '/working-time-models', label: 'Working Time Models', admin: true },
];

export function AppShell() {
  const { user, logout, isAdmin } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Zytlog</div>
        <ul className="nav-list">
          {navItems
            .filter((item) => !item.admin || isAdmin)
            .map((item) => (
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
