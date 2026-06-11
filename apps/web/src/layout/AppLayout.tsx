import { Link, Outlet } from 'react-router-dom';
import { phase4Routes } from '../routes';
import { getApiBaseUrl } from '../api/client';
import { clearSession, getStoredUser } from '../auth/token';

export function AppLayout() {
  const user = getStoredUser();

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', minHeight: '100vh' }}>
      <aside style={{ padding: '1rem', borderRight: '1px solid #ddd' }}>
        <h1 style={{ fontSize: '1.1rem' }}>TerraForge Web</h1>
        <p style={{ fontSize: '0.85rem' }}>API: {getApiBaseUrl()}</p>
        {user ? (
          <p style={{ fontSize: '0.85rem' }}>
            {String(user.email)} ({String(user.role)})
          </p>
        ) : (
          <Link to="/login">Sign in</Link>
        )}
        {user && (
          <button type="button" onClick={() => clearSession()} style={{ marginTop: '0.5rem' }}>
            Sign out
          </button>
        )}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {phase4Routes.map((route) => (
            <Link key={route.path} to={route.path}>
              {route.page}
            </Link>
          ))}
        </nav>
      </aside>
      <main style={{ padding: '1.5rem' }}>
        <Outlet />
      </main>
    </div>
  );
}