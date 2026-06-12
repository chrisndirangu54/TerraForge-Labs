import { NavLink, Outlet } from 'react-router-dom';
import { getApiBaseUrl } from '../api/client';
import { Button } from '../components/ui/Button';
import { iconForPage, NavIcon } from '../components/ui/NavIcon';
import { clearSession, getStoredUser } from '../auth/token';
import { phase4Routes } from '../routes';

const DOMAIN_LABELS: Record<string, string> = {
  core: 'Mission Control',
  geology: 'Geology & ML',
  hydrogeology: 'Hydrogeology',
  urban: 'Urban',
  infrastructure: 'Infrastructure',
  satellite: 'Remote Sensing',
  admin: 'Administration',
};

const DOMAIN_ACCENT: Record<string, string> = {
  core: 'text-mineral-500',
  geology: 'text-ore-500',
  hydrogeology: 'text-mineral-400',
  satellite: 'text-mineral-400',
  urban: 'text-strata-400',
  infrastructure: 'text-sediment-dim',
  admin: 'text-sediment-dim',
};

const DOMAIN_ORDER = [
  'core',
  'geology',
  'hydrogeology',
  'satellite',
  'urban',
  'infrastructure',
  'admin',
];

function navLinkClass({ isActive }: { isActive: boolean }) {
  return [
    'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-all duration-200 ease-smooth',
    isActive
      ? 'bg-forge-700/90 text-ore-300 shadow-glow-ore border border-ore-500/20'
      : 'text-sediment-muted hover:bg-forge-800/80 hover:text-sediment border border-transparent',
  ].join(' ');
}

export function AppLayout() {
  const user = getStoredUser();
  const grouped = DOMAIN_ORDER.map((domain) => ({
    domain,
    label: DOMAIN_LABELS[domain] ?? domain,
    routes: phase4Routes.filter((r) => r.domain === domain),
  })).filter((g) => g.routes.length > 0);

  return (
    <div className="flex min-h-screen">
      <aside className="relative flex w-64 shrink-0 flex-col border-r border-forge-600/60 bg-forge-900/80 shadow-panel backdrop-blur-xl">
        <div className="pointer-events-none absolute inset-0 bg-terrain-grid bg-grid opacity-20" aria-hidden />
        <div className="relative border-b border-forge-600/50 p-4">
          <div className="flex items-center gap-3">
            <div
              className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-ore-500/50 bg-gradient-to-br from-forge-800 to-forge-900 font-display text-lg font-bold text-ore-400 shadow-glow-ore"
              aria-hidden
            >
              TF
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse-glow rounded-full bg-moss-500 shadow-[0_0_6px_rgba(90,122,82,0.8)]" />
            </div>
            <div>
              <h1 className="font-display text-lg font-bold leading-tight tracking-wider text-sediment">
                TerraForge
              </h1>
              <p className="font-mono text-[10px] uppercase tracking-widest text-mineral-500">
                Exploration Labs
              </p>
            </div>
          </div>
        </div>

        <div className="relative border-b border-forge-600/40 px-4 py-3">
          <p className="tf-label">API endpoint</p>
          <p className="mt-1 truncate rounded-md border border-forge-600/40 bg-forge-950/50 px-2 py-1 font-mono text-[11px] text-mineral-400">
            {getApiBaseUrl()}
          </p>
          {user ? (
            <div className="mt-3 rounded-lg border border-forge-600/40 bg-forge-850/50 p-2.5">
              <p className="truncate text-xs text-sediment">{String(user.email)}</p>
              <span className="tf-badge-ore mt-1.5">{String(user.role)}</span>
            </div>
          ) : (
            <NavLink to="/login" className="tf-link mt-2 inline-block text-sm">
              Sign in →
            </NavLink>
          )}
          {user ? (
            <Button
              variant="ghost"
              className="mt-2 w-full text-xs"
              onClick={() => clearSession()}
            >
              Sign out
            </Button>
          ) : null}
        </div>

        <nav className="relative flex-1 overflow-y-auto px-3 py-4">
          {grouped.map((group) => (
            <div key={group.domain} className="mb-5">
              <p className={`tf-label mb-2 px-2 ${DOMAIN_ACCENT[group.domain] ?? ''}`}>
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.routes.map((route) => {
                  const iconName = iconForPage(route.page);
                  return (
                    <li key={route.path}>
                      <NavLink to={route.path} className={navLinkClass} end={route.path === '/'}>
                        <span className="tf-nav-icon group-hover:border-mineral-500/30 group-hover:text-mineral-400">
                          <NavIcon name={iconName} />
                        </span>
                        <span className="truncate">{route.page}</span>
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="relative border-t border-forge-600/40 p-4">
          <p className="font-mono text-[10px] text-sediment-dim">v0.2 · Matuu-Kwale corridor</p>
        </div>
      </aside>

      <main className="relative flex-1 overflow-auto">
        <div
          className="pointer-events-none absolute inset-0 bg-terrain-grid bg-grid opacity-50"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-0 bg-contour-lines bg-contour opacity-80"
          aria-hidden
        />
        <div className="pointer-events-none absolute inset-0 bg-strata-gradient" aria-hidden />
        <div className="relative px-6 py-8 md:px-10 md:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}