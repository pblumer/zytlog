import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate, type NavLinkRenderProps } from 'react-router-dom';

import { useAuth } from '../auth/provider';
import { getDefaultRouteForRole, getNavItemsByRole, isManagedAppPath, isPathAllowedForRole } from '../auth/roleRouting';

function HamburgerIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="5" x2="17" y2="5" />
      <line x1="3" y1="10" x2="17" y2="10" />
      <line x1="3" y1="15" x2="17" y2="15" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="5" y1="5" x2="15" y2="15" />
      <line x1="15" y1="5" x2="5" y2="15" />
    </svg>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const navItems = getNavItemsByRole(user?.role);
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!menuOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [menuOpen]);

  useEffect(() => {
    if (!user?.role) {
      return;
    }

    if (!isManagedAppPath(pathname)) {
      return;
    }

    if (isPathAllowedForRole(pathname, user.role)) {
      return;
    }

    navigate(getDefaultRouteForRole(user.role), { replace: true });
  }, [navigate, pathname, user?.role]);

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Zum Hauptinhalt springen
      </a>

      {menuOpen ? <button type="button" className="nav-backdrop" aria-label="Menü schliessen" onClick={() => setMenuOpen(false)} /> : null}

      <aside className={`sidebar${menuOpen ? ' open' : ''}`} id="main-navigation">
        <div className="sidebar-head">
          <div className="brand">Zytlog</div>
          <button type="button" className="btn outline sidebar-close" onClick={() => setMenuOpen(false)} aria-label="Menü schliessen">
            <CloseIcon />
          </button>
        </div>
        <ul className="nav-list">
          {user?.role === 'admin' || user?.role === 'system_admin' ? <li className="meta">Verwaltung</li> : null}
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end
                className={({ isActive }: NavLinkRenderProps) => `nav-link${isActive ? ' active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </aside>

      <div className="main-region">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="btn outline menu-toggle"
              aria-label="Menü öffnen"
              aria-controls="main-navigation"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <HamburgerIcon />
            </button>
            <div>
              <strong>{user?.username ?? user?.email}</strong>
              <div className="meta">Role: {user?.role ?? 'unknown'}</div>
            </div>
          </div>
          <button className="btn outline" onClick={logout}>
            Logout
          </button>
        </header>

        <main className="page" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}